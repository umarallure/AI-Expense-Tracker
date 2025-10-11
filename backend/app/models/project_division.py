from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
from app.db.base import Base


class ProjectDivision(Base):
    __tablename__ = 'project_divisions'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    business_id = Column(String, ForeignKey('businesses.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code like #FF5733
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    business = relationship("Business", back_populates="project_divisions")
    transactions = relationship("Transaction", back_populates="project_division")
    documents = relationship("Document", back_populates="project_division")

    def __repr__(self):
        return f"<ProjectDivision(id='{self.id}', name='{self.name}', business_id='{self.business_id}')>"