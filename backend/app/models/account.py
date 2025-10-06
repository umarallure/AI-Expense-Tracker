"""
SQLAlchemy models for Account-related database tables.
Defines the Account model with relationships and constraints.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Integer, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from uuid import uuid4
import enum


class AccountType(enum.Enum):
    """Enumeration of account types."""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    LOAN = "loan"
    CASH = "cash"
    OTHER = "other"


class Account(Base):
    """Account model representing financial accounts."""
    __tablename__ = 'accounts'

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    business_id = Column(String, ForeignKey('businesses.id'), nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String, nullable=False)  # Using string to match enum
    currency = Column(String(3), nullable=False, default='USD')
    description = Column(Text, nullable=True)
    institution_name = Column(String(255), nullable=True)
    account_number_masked = Column(String(50), nullable=True)
    routing_number = Column(String(50), nullable=True)
    current_balance = Column(Numeric(15, 2), nullable=False, default=0.00)
    available_balance = Column(Numeric(15, 2), nullable=True)
    credit_limit = Column(Numeric(15, 2), nullable=True)
    interest_rate = Column(Numeric(7, 4), nullable=True)
    minimum_payment = Column(Numeric(15, 2), nullable=True)
    due_date = Column(Integer, nullable=True)  # Day of month (1-31)
    is_primary = Column(Boolean, nullable=False, default=False)
    color = Column(String(7), nullable=True)  # Hex color code
    icon = Column(String(50), nullable=True)
    settings = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    business = relationship("Business", back_populates="accounts")
    # transactions relationship will be added when transactions are implemented

    # Indexes
    __table_args__ = (
        Index('idx_accounts_business_active', 'business_id', 'is_active'),
        Index('idx_accounts_type', 'account_type'),
        Index('idx_accounts_currency', 'currency'),
    )

    def __repr__(self):
        return f"<Account(id='{self.id}', name='{self.account_name}', type='{self.account_type}')>"