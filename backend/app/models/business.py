from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Text, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
from app.db.base import Base
import enum


class BusinessType(str, enum.Enum):
    """Enumeration of business types."""
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    PARTNERSHIP = "partnership"
    LLC = "llc"
    CORPORATION = "corporation"
    S_CORP = "s_corp"
    NON_PROFIT = "non_profit"
    OTHER = "other"


class BusinessStatus(str, enum.Enum):
    """Enumeration of business statuses."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class Business(Base):
    __tablename__ = 'businesses'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    owner_id = Column(String, nullable=False, index=True)  # Reference to user who owns the business
    business_name = Column(String(255), nullable=False)
    business_type = Column(String, nullable=True)
    industry = Column(String(100), nullable=True)
    tax_id = Column(String(100), nullable=True)
    currency = Column(String(3), nullable=False, default='USD')
    fiscal_year_start = Column(Integer, nullable=False, default=1)  # Month (1-12)
    timezone = Column(String(100), nullable=False, default='UTC')
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String, nullable=True)
    website = Column(String(255), nullable=True)
    logo_url = Column(String, nullable=True)
    settings = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False, default='active')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    members = relationship("BusinessMember", back_populates="business")
    accounts = relationship("Account", back_populates="business")
    categories = relationship("Category", back_populates="business")
    transactions = relationship("Transaction", back_populates="business")

    def __repr__(self):
        return f"<Business(id='{self.id}', name='{self.business_name}')>"


class MemberRole(str, enum.Enum):
    """Enumeration of business member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


class MemberStatus(str, enum.Enum):
    """Enumeration of member statuses."""
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"


class BusinessMember(Base):
    __tablename__ = 'business_members'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    business_id = Column(String, ForeignKey('businesses.id'), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)  # Reference to user
    role = Column(String, nullable=False, default='viewer')
    permissions = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False, default='active')
    invited_by = Column(String, nullable=True)
    invited_at = Column(DateTime(timezone=True), nullable=True)
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    business = relationship("Business", back_populates="members")

    def __repr__(self):
        return f"<BusinessMember(id='{self.id}', business_id='{self.business_id}', user_id='{self.user_id}', role='{self.role}')>"