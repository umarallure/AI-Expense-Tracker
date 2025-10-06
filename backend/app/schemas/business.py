"""
Pydantic schemas for Business-related API requests and responses.
Defines data validation and serialization for business operations.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class BusinessType(str, Enum):
    """Enumeration of business types."""
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    PARTNERSHIP = "partnership"
    LLC = "llc"
    CORPORATION = "corporation"
    S_CORP = "s_corp"
    NON_PROFIT = "non_profit"
    OTHER = "other"


class BusinessStatus(str, Enum):
    """Enumeration of business statuses."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class MemberRole(str, Enum):
    """Enumeration of business member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


class MemberStatus(str, Enum):
    """Enumeration of member statuses."""
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"


# ============================================================================
# Business Schemas
# ============================================================================

class BusinessBase(BaseModel):
    """Base schema for business with common fields."""
    business_name: str = Field(..., min_length=1, max_length=255)
    business_type: Optional[BusinessType] = None
    industry: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=100)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    fiscal_year_start: int = Field(default=1, ge=1, le=12)
    timezone: str = Field(default="UTC", max_length=100)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    settings: Dict[str, Any] = Field(default_factory=dict)


class BusinessCreate(BusinessBase):
    """Schema for creating a new business."""
    pass


class BusinessUpdate(BaseModel):
    """Schema for updating an existing business (all fields optional)."""
    business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    business_type: Optional[BusinessType] = None
    industry: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=100)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    fiscal_year_start: Optional[int] = Field(None, ge=1, le=12)
    timezone: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    status: Optional[BusinessStatus] = None


class BusinessResponse(BusinessBase):
    """Schema for business response with all fields."""
    id: str
    owner_id: str
    logo_url: Optional[str] = None
    status: BusinessStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BusinessListResponse(BaseModel):
    """Schema for paginated list of businesses."""
    businesses: list[BusinessResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Business Member Schemas
# ============================================================================

class BusinessMemberBase(BaseModel):
    """Base schema for business member."""
    role: MemberRole = Field(default=MemberRole.VIEWER)
    permissions: Dict[str, Any] = Field(default_factory=dict)


class BusinessMemberInvite(BaseModel):
    """Schema for inviting a new member to a business."""
    email: EmailStr
    role: MemberRole = Field(default=MemberRole.VIEWER)
    permissions: Dict[str, Any] = Field(default_factory=dict)


class BusinessMemberCreate(BusinessMemberBase):
    """Schema for creating a business member (internal use)."""
    business_id: str
    user_id: str


class BusinessMemberUpdate(BaseModel):
    """Schema for updating a business member."""
    role: Optional[MemberRole] = None
    permissions: Optional[Dict[str, Any]] = None
    status: Optional[MemberStatus] = None


class BusinessMemberResponse(BusinessMemberBase):
    """Schema for business member response."""
    id: str
    business_id: str
    user_id: str
    status: MemberStatus
    invited_by: Optional[str] = None
    invited_at: Optional[datetime] = None
    joined_at: datetime
    last_active_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Optional: Include user details
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class BusinessMemberListResponse(BaseModel):
    """Schema for list of business members."""
    members: list[BusinessMemberResponse]
    total: int


# ============================================================================
# Combined Response Schemas
# ============================================================================

class BusinessWithMembers(BusinessResponse):
    """Schema for business with its members."""
    members: list[BusinessMemberResponse] = []
    member_count: int = 0


class BusinessDashboard(BaseModel):
    """Schema for business dashboard summary."""
    business: BusinessResponse
    member_count: int
    recent_activity: list[Dict[str, Any]] = []
    statistics: Dict[str, Any] = Field(default_factory=dict)
