from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, Text, Boolean, UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum
from uuid import uuid4

class TransactionType(enum.Enum):
    income = "income"
    expense = "expense"
    transfer = "transfer"

class ExpenseStatus(enum.Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    description = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    receipt_url = Column(String, nullable=True)
    status = Column(Enum(ExpenseStatus), nullable=False, default=ExpenseStatus.draft)
    notes = Column(Text, nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relationships
    category = relationship("Category", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    business = relationship("Business", back_populates="transactions")