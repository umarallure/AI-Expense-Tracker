"""
Pydantic schemas for Project Division-related API requests and responses.
Defines data validation and serialization for project division operations.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID


# ============================================================================
# Project Division Schemas
# ============================================================================

class ProjectDivisionBase(BaseModel):
    """Base schema for project division with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')  # Hex color validation
    is_active: bool = Field(default=True)


class ProjectDivisionCreate(ProjectDivisionBase):
    """Schema for creating a new project division."""
    business_id: str


class ProjectDivisionUpdate(BaseModel):
    """Schema for updating an existing project division (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')  # Hex color validation
    is_active: Optional[bool] = None


class ProjectDivisionResponse(ProjectDivisionBase):
    """Schema for project division response with all fields."""
    id: str
    business_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectDivisionListResponse(BaseModel):
    """Schema for paginated list of project divisions."""
    divisions: list[ProjectDivisionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProjectDivisionWithStats(ProjectDivisionResponse):
    """Schema for project division with statistics."""
    transaction_count: int = 0
    document_count: int = 0
    total_amount: float = 0.0


class ProjectDivisionStats(BaseModel):
    """Schema for project division statistics."""
    division_id: str
    transaction_count: int
    document_count: int
    total_income: float
    total_expenses: float
    net_amount: float