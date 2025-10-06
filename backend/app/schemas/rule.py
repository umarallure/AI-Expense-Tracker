from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class RuleType(str, Enum):
    AUTO_CATEGORIZE = "auto_categorize"
    AUTO_TAG = "auto_tag"
    APPROVAL_REQUIRED = "approval_required"
    FLAG_SUSPICIOUS = "flag_suspicious"

class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"

class RuleCondition(BaseModel):
    field: str = Field(..., description="Field to check (e.g., 'description', 'amount', 'category_id')")
    operator: ConditionOperator
    value: Any = Field(..., description="Value to compare against")

class RuleAction(BaseModel):
    type: str = Field(..., description="Action type (e.g., 'set_category', 'add_tag', 'require_approval')")
    value: Any = Field(..., description="Action value (e.g., category_id, tag_name)")

class RuleBase(BaseModel):
    business_id: str
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    rule_type: RuleType
    conditions: List[RuleCondition] = Field(..., min_items=1)
    actions: List[RuleAction] = Field(..., min_items=1)
    priority: int = Field(default=0, ge=0, le=100, description="Rule priority (higher numbers = higher priority)")
    is_active: bool = True

class RuleCreate(RuleBase):
    pass

class RuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    rule_type: Optional[RuleType] = None
    conditions: Optional[List[RuleCondition]] = Field(None, min_items=1)
    actions: Optional[List[RuleAction]] = Field(None, min_items=1)
    priority: Optional[int] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None

class Rule(RuleBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True