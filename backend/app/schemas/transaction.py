from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import enum

class ExpenseStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class TransactionBase(BaseModel):
    business_id: UUID
    account_id: UUID
    category_id: Optional[UUID] = None
    user_id: Optional[UUID] = None  # Will be set by the endpoint
    amount: float
    currency: str = "USD"
    description: str
    date: datetime
    is_income: bool = False
    receipt_url: Optional[str] = None
    status: ExpenseStatus = ExpenseStatus.draft
    notes: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    vendor: Optional[str] = None
    taxes_fees: Optional[float] = None
    payment_method: Optional[str] = None
    recipient_id: Optional[str] = None

class TransactionCreate(TransactionBase):
    status: ExpenseStatus = ExpenseStatus.pending  # Default to pending for approval workflow
    user_id: Optional[UUID] = None  # Not required in request, will be set by endpoint

class TransactionUpdate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TransactionList(BaseModel):
    transactions: List[Transaction]
    total: int

class TransactionApproval(BaseModel):
    status: ExpenseStatus
    approval_notes: Optional[str] = None

class TransactionApprovalUpdate(BaseModel):
    business_id: UUID
    account_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    is_income: Optional[bool] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None
    status: ExpenseStatus
    approval_notes: Optional[str] = None
    vendor: Optional[str] = None
    taxes_fees: Optional[float] = None
    payment_method: Optional[str] = None
    recipient_id: Optional[str] = None