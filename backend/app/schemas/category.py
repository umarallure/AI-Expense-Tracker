"""
Pydantic schemas for Category-related API requests and responses.
Defines data validation and serialization for category operations.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from decimal import Decimal


class CategoryType(str, Enum):
    """Enumeration of category types."""
    INCOME = "income"
    EXPENSE = "expense"


# ============================================================================
# Category Schemas
# ============================================================================

class CategoryBase(BaseModel):
    """Base schema for category with common fields."""
    category_name: str = Field(..., min_length=1, max_length=255)
    category_type: CategoryType
    is_income: bool = Field(default=False)
    description: Optional[str] = Field(None, max_length=1000)
    parent_id: Optional[str] = None
    display_order: int = Field(default=0, ge=0)
    color: Optional[str] = Field(None, max_length=7)  # Hex color code
    icon: Optional[str] = Field(None, max_length=50)
    settings: Dict[str, Any] = Field(default_factory=dict)

    @validator('color')
    def validate_color(cls, v):
        """Validate hex color format."""
        if v and not v.startswith('#'):
            raise ValueError('Color must be a valid hex color code starting with #')
        if v and len(v) != 7:
            raise ValueError('Color must be a 7-character hex color code')
        return v


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    business_id: str
    is_system: bool = Field(default=False)


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category (all fields optional)."""
    category_name: Optional[str] = Field(None, min_length=1, max_length=255)
    category_type: Optional[CategoryType] = None
    is_income: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=1000)
    parent_id: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)
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


class CategoryResponse(CategoryBase):
    """Schema for category response with all fields."""
    id: str
    business_id: str
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    """Schema for paginated list of categories."""
    categories: list[CategoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CategorySummary(BaseModel):
    """Schema for category summary with calculated fields."""
    id: str
    business_id: str
    category_name: str
    category_type: CategoryType
    parent_id: Optional[str]
    is_system: bool
    color: Optional[str]
    icon: Optional[str]
    created_at: datetime
    updated_at: datetime
    transaction_count: int = Field(default=0)
    total_income: Decimal = Field(default=Decimal('0.00'))
    total_expenses: Decimal = Field(default=Decimal('0.00'))
    net_amount: Decimal = Field(default=Decimal('0.00'))

    class Config:
        from_attributes = True


class CategoryTreeNode(CategoryResponse):
    """Schema for category tree node with children."""
    children: List['CategoryTreeNode'] = []
    transaction_count: int = 0
    total_amount: Decimal = Field(default=Decimal('0.00'))


# Update forward reference
CategoryTreeNode.update_forward_refs()


# ============================================================================
# Category Transaction Schemas (for future integration)
# ============================================================================

class CategoryTransactionSummary(BaseModel):
    """Schema for category transaction summary."""
    category_id: str
    transaction_count: int = 0
    total_income: Decimal = Field(default=Decimal('0.00'))
    total_expenses: Decimal = Field(default=Decimal('0.00'))
    net_amount: Decimal = Field(default=Decimal('0.00'))
    last_transaction_date: Optional[datetime] = None


# ============================================================================
# Combined Response Schemas
# ============================================================================

class CategoryWithTransactions(CategoryResponse):
    """Schema for category with transaction summary."""
    transaction_summary: CategoryTransactionSummary


class CategoryHierarchy(BaseModel):
    """Schema for category hierarchy/tree structure."""
    root_categories: List[CategoryTreeNode]
    total_categories: int


class BusinessCategoriesSummary(BaseModel):
    """Schema for business categories summary."""
    business_id: str
    total_categories: int
    system_categories: int
    custom_categories: int
    income_categories: int
    expense_categories: int
    total_income: Decimal = Field(default=Decimal('0.00'))
    total_expenses: Decimal = Field(default=Decimal('0.00'))
    net_profit: Decimal = Field(default=Decimal('0.00'))
    categories: List[CategorySummary] = []


# ============================================================================
# Bulk Operations Schemas
# ============================================================================

class CategoryBulkCreate(BaseModel):
    """Schema for bulk creating categories."""
    categories: List[CategoryCreate]


class CategoryBulkUpdate(BaseModel):
    """Schema for bulk updating categories."""
    updates: Dict[str, CategoryUpdate]  # category_id -> update data


class CategoryBulkDelete(BaseModel):
    """Schema for bulk deleting categories."""
    category_ids: List[str]


# ============================================================================
# Default Categories Schema
# ============================================================================

class DefaultCategoryTemplate(BaseModel):
    """Schema for default category template."""
    category_name: str
    category_type: CategoryType
    description: str
    display_order: int
    color: str
    icon: str


class DefaultCategoriesResponse(BaseModel):
    """Schema for default categories response."""
    income_categories: List[DefaultCategoryTemplate]
    expense_categories: List[DefaultCategoryTemplate]