"""
FastAPI dependencies for dependency injection.
Common dependencies used across the application.
"""
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user
from app.db.supabase import get_supabase_client
from supabase import Client


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Dependency to get current active user."""
    return current_user


async def get_supabase_dependency() -> Client:
    """Dependency to get Supabase client instance."""
    return get_supabase_client()


async def get_business_access(
    business_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_dependency)
) -> Dict[str, Any]:
    """Verify user has access to a specific business."""
    user_id = current_user.get("user_id")
    
    response = supabase.table("business_members").select("*").eq(
        "business_id", business_id
    ).eq("user_id", user_id).eq("status", "active").execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this business"
        )
    
    member = response.data[0]
    return {
        "business_id": business_id,
        "user_id": user_id,
        "role": member.get("role", "viewer"),
        "member_id": member.get("id")
    }


def check_business_permission(required_permission: str):
    """Dependency factory to check specific business permissions."""
    async def permission_checker(
        business_access: Dict = Depends(get_business_access)
    ) -> Dict:
        role = business_access.get("role", "viewer")
        
        permission_levels = {
            "owner": 4,
            "admin": 3,
            "accountant": 2,
            "viewer": 1
        }
        
        user_level = permission_levels.get(role, 0)
        required_level = permission_levels.get(required_permission, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission}"
            )
        
        return business_access
    
    return permission_checker


class Pagination:
    """Pagination dependency for list endpoints."""
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), max_page_size)
        self.offset = (self.page - 1) * self.page_size
        
    @property
    def limit(self) -> int:
        return self.page_size
    
    def get_pagination_metadata(self, total_count: int) -> Dict[str, Any]:
        """Generate pagination metadata for response."""
        total_pages = (total_count + self.page_size - 1) // self.page_size
        
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": self.page < total_pages,
            "has_prev": self.page > 1
        }


# Service dependencies (to be implemented later)
def get_ai_extractor():
    """Get AI extractor service instance."""
    from app.services.ai_extractor import AIExtractor
    return AIExtractor()


def get_rule_engine():
    """Get rule engine service instance."""
    from app.services.rule_engine import RuleEngine
    return RuleEngine()


def get_report_generator():
    """Get report generator service instance."""
    from app.services.report_generator import ReportGenerator
    return ReportGenerator()


def get_embeddings_service():
    """Get embeddings service instance."""
    from app.services.embeddings import EmbeddingsService
    return EmbeddingsService()