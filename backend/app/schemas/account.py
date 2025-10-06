"""
Pydantic schemas for Account-related API requests and responses.
Defines data validation and serialization for account operations.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from decimal import Decimal


class AccountType(str, Enum):
    """Enumeration of account types."""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    LOAN = "loan"
    CASH = "cash"
    OTHER = "other"


class AccountStatus(str, Enum):
    """Enumeration of account statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"


# ============================================================================
# Account Schemas
# ============================================================================

class AccountBase(BaseModel):
    """Base schema for account with common fields."""
    account_name: str = Field(..., min_length=1, max_length=255)
    account_type: AccountType
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: Optional[str] = Field(None, max_length=1000)
    institution_name: Optional[str] = Field(None, max_length=255)
    account_number_masked: Optional[str] = Field(None, max_length=50)
    routing_number: Optional[str] = Field(None, max_length=50)
    current_balance: Decimal = Field(default=Decimal('0.00'), decimal_places=2)
    available_balance: Optional[Decimal] = Field(None, decimal_places=2)
    credit_limit: Optional[Decimal] = Field(None, decimal_places=2)
    interest_rate: Optional[Decimal] = Field(None, decimal_places=4)
    minimum_payment: Optional[Decimal] = Field(None, decimal_places=2)
    due_date: Optional[int] = Field(None, ge=1, le=31)  # Day of month
    is_primary: bool = Field(default=False)
    color: Optional[str] = Field(None, max_length=7)  # Hex color code
    icon: Optional[str] = Field(None, max_length=50)
    settings: Dict[str, Any] = Field(default_factory=dict)

    @validator('available_balance', always=True)
    def set_available_balance(cls, v, values):
        """Set available_balance to current_balance if not provided."""
        if v is None and 'current_balance' in values:
            return values['current_balance']
        return v

    @validator('color')
    def validate_color(cls, v):
        """Validate hex color format."""
        if v and not v.startswith('#'):
            raise ValueError('Color must be a valid hex color code starting with #')
        if v and len(v) != 7:
            raise ValueError('Color must be a 7-character hex color code')
        return v


class AccountCreate(AccountBase):
    """Schema for creating a new account."""
    business_id: str


class AccountUpdate(BaseModel):
    """Schema for updating an existing account (all fields optional)."""
    account_name: Optional[str] = Field(None, min_length=1, max_length=255)
    account_type: Optional[AccountType] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    description: Optional[str] = Field(None, max_length=1000)
    institution_name: Optional[str] = Field(None, max_length=255)
    account_number_masked: Optional[str] = Field(None, max_length=50)
    routing_number: Optional[str] = Field(None, max_length=50)
    current_balance: Optional[Decimal] = Field(None, decimal_places=2)
    available_balance: Optional[Decimal] = Field(None, decimal_places=2)
    credit_limit: Optional[Decimal] = Field(None, decimal_places=2)
    interest_rate: Optional[Decimal] = Field(None, decimal_places=4)
    minimum_payment: Optional[Decimal] = Field(None, decimal_places=2)
    due_date: Optional[int] = Field(None, ge=1, le=31)
    is_primary: Optional[bool] = None
    color: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @validator('color')
    def validate_color(cls, v):
        """Validate hex color format."""
        if v and not v.startswith('#'):
            raise ValueError('Color must be a valid hex color code starting with #')
        if v and len(v) != 7:
            raise ValueError('Color must be a 7-character hex color code')
        return v


class AccountResponse(AccountBase):
    """Schema for account response with all fields."""
    id: str
    business_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccountListResponse(BaseModel):
    """Schema for paginated list of accounts."""
    accounts: list[AccountResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AccountSummary(BaseModel):
    """Schema for account summary with calculated fields."""
    id: str
    business_id: str
    account_name: str
    account_type: AccountType
    currency: str
    current_balance: Decimal
    available_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    total_debits: Decimal = Field(default=Decimal('0.00'))
    total_credits: Decimal = Field(default=Decimal('0.00'))
    net_flow: Decimal = Field(default=Decimal('0.00'))

    class Config:
        from_attributes = True


class AccountBalanceUpdate(BaseModel):
    """Schema for updating account balance."""
    current_balance: Decimal = Field(..., decimal_places=2)
    available_balance: Optional[Decimal] = Field(None, decimal_places=2)


# ============================================================================
# Account Transaction Schemas (for future integration)
# ============================================================================

class AccountTransactionSummary(BaseModel):
    """Schema for account transaction summary."""
    account_id: str
    total_transactions: int = 0
    total_debits: Decimal = Field(default=Decimal('0.00'))
    total_credits: Decimal = Field(default=Decimal('0.00'))
    net_flow: Decimal = Field(default=Decimal('0.00'))
    last_transaction_date: Optional[datetime] = None


# ============================================================================
# Combined Response Schemas
# ============================================================================

class AccountWithTransactions(AccountResponse):
    """Schema for account with transaction summary."""
    transaction_summary: AccountTransactionSummary


class BusinessAccountsSummary(BaseModel):
    """Schema for business accounts summary."""
    business_id: str
    total_accounts: int
    active_accounts: int
    total_balance: Decimal = Field(default=Decimal('0.00'))
    total_available_balance: Decimal = Field(default=Decimal('0.00'))
    accounts: List[AccountSummary] = []
