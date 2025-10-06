"""
SQLAlchemy models for Category-related database tables.
Defines the Category model with relationships and constraints.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from uuid import uuid4
import enum


class CategoryType(enum.Enum):
    """Enumeration of category types."""
    INCOME = "income"
    EXPENSE = "expense"


class Category(Base):
    """Category model representing transaction categories."""
    __tablename__ = 'categories'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    business_id = Column(String, ForeignKey('businesses.id'), nullable=False, index=True)
    category_name = Column(String(255), nullable=False)
    category_type = Column(String, nullable=False)  # Using string to match enum
    description = Column(Text, nullable=True)
    parent_id = Column(String, ForeignKey('categories.id'), nullable=True, index=True)
    display_order = Column(Integer, nullable=False, default=0)
    is_system = Column(Boolean, nullable=False, default=False)
    color = Column(String(7), nullable=True)  # Hex color code
    icon = Column(String(50), nullable=True)
    settings = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    business = relationship("Business", back_populates="categories")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    # transactions relationship will be added when transactions are implemented

    # Indexes
    __table_args__ = (
        Index('idx_categories_business_active', 'business_id', 'is_active'),
        Index('idx_categories_type', 'category_type'),
        Index('idx_categories_parent', 'parent_id'),
        Index('idx_categories_display_order', 'business_id', 'display_order'),
    )

    def __repr__(self):
        return f"<Category(id='{self.id}', name='{self.category_name}', type='{self.category_type}')>"