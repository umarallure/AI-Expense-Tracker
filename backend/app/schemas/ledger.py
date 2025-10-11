"""
Pydantic schemas for Ledger-related API requests and responses.
Defines data validation and serialization for ledger operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Annotated
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class LedgerEntryBase(BaseModel):
    """Base schema for ledger entry."""
    business_id: UUID
    account_id: UUID
    transaction_id: UUID
    amount_before: Annotated[Decimal, Field(..., ge=Decimal('-999999999.99'), le=Decimal('999999999.99'))]
    amount_after: Annotated[Decimal, Field(..., ge=Decimal('-999999999.99'), le=Decimal('999999999.99'))]
    change_amount: Annotated[Decimal, Field(..., ge=Decimal('-999999999.99'), le=Decimal('999999999.99'))]
    transaction_type: str = Field(..., regex=r'^(income|expense)$')
    description: Optional[str] = None
    created_by: UUID


class LedgerEntryCreate(LedgerEntryBase):
    """Schema for creating a ledger entry."""
    pass


class LedgerEntryResponse(LedgerEntryBase):
    """Schema for ledger entry response."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class LedgerEntryList(BaseModel):
    """Schema for paginated list of ledger entries."""
    entries: List[LedgerEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AccountBalanceHistory(BaseModel):
    """Schema for account balance history."""
    account_id: UUID
    balance_history: List[LedgerEntryResponse]
    current_balance: Decimal
    total_changes: int


class LedgerSummary(BaseModel):
    """Schema for ledger summary statistics."""
    business_id: UUID
    total_entries: int
    total_income_amount: Decimal
    total_expense_amount: Decimal
    net_change: Decimal
    date_range: Optional[dict] = None