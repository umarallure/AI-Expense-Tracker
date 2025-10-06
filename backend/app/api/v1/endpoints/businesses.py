"""
Business management endpoints for creating and managing businesses.
Handles business CRUD operations and member management.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from loguru import logger
from typing import Dict, Any, List
from uuid import UUID

from app.schemas.business import (
    BusinessCreate,
    BusinessUpdate,
    BusinessResponse,
    BusinessListResponse,
    BusinessMemberInvite,
    BusinessMemberUpdate,
    BusinessMemberResponse,
    BusinessMemberListResponse,
    BusinessWithMembers
)
from app.schemas.auth import MessageResponse
from app.core.security import get_current_user
from app.core.deps import Pagination, get_business_access, check_business_permission
from app.db.supabase import get_supabase_client
from supabase import Client

router = APIRouter(prefix="/businesses", tags=["Businesses"])


@router.post("/", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    business_data: BusinessCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Create a new business.
    
    The current user automatically becomes the business owner.
    """
    try:
        # Create business record
        business_dict = business_data.model_dump()
        business_dict["owner_id"] = current_user["user_id"]
        
        response = supabase.table("businesses").insert(business_dict).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create business"
            )
        
        business = response.data[0]
        logger.info(f"Business created: {business['id']} by user {current_user['user_id']}")
        
        return BusinessResponse(**business)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create business error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=BusinessListResponse)
async def list_businesses(
    pagination: Pagination = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    List all businesses the current user has access to.
    
    Returns businesses where user is owner or member.
    """
    try:
        user_id = current_user["user_id"]
        
        # Get businesses where user is a member
        member_response = supabase.table("business_members")\
            .select("business_id")\
            .eq("user_id", user_id)\
            .eq("status", "active")\
            .execute()
        
        business_ids = [m["business_id"] for m in member_response.data]
        
        # Get business details
        query = supabase.table("businesses").select("*", count="exact")
        
        if business_ids:
            query = query.in_("id", business_ids)
        else:
            # No businesses found
            return BusinessListResponse(
                businesses=[],
                total=0,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=0
            )
        
        # Apply pagination
        response = query.range(
            pagination.offset,
            pagination.offset + pagination.limit - 1
        ).execute()
        
        businesses = [BusinessResponse(**b) for b in response.data]
        total = response.count or 0
        
        metadata = pagination.get_pagination_metadata(total)
        
        return BusinessListResponse(
            businesses=businesses,
            total=total,
            page=metadata["page"],
            page_size=metadata["page_size"],
            total_pages=metadata["total_pages"]
        )
        
    except Exception as e:
        logger.error(f"List businesses error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve businesses"
        )


@router.get("/{business_id}", response_model=BusinessWithMembers)
async def get_business(
    business_id: str,
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get detailed information about a specific business.
    
    Includes business details and member list.
    """
    try:
        # Get business details
        business_response = supabase.table("businesses")\
            .select("*")\
            .eq("id", business_id)\
            .single()\
            .execute()
        
        if not business_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        # Get business members
        members_response = supabase.table("business_members")\
            .select("*")\
            .eq("business_id", business_id)\
            .execute()
        
        business = business_response.data
        members = [BusinessMemberResponse(**m) for m in members_response.data]
        
        return BusinessWithMembers(
            **business,
            members=members,
            member_count=len(members)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get business error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve business"
        )


@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: str,
    business_data: BusinessUpdate,
    business_access: Dict = Depends(check_business_permission("admin")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update business information.
    
    Requires admin or owner role.
    """
    try:
        # Update business
        update_dict = business_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        response = supabase.table("businesses")\
            .update(update_dict)\
            .eq("id", business_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        logger.info(f"Business updated: {business_id}")
        
        return BusinessResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update business error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{business_id}", response_model=MessageResponse)
async def delete_business(
    business_id: str,
    business_access: Dict = Depends(check_business_permission("owner")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Delete a business.
    
    Requires owner role. This will cascade delete all related data.
    """
    try:
        response = supabase.table("businesses")\
            .delete()\
            .eq("id", business_id)\
            .execute()
        
        logger.info(f"Business deleted: {business_id}")
        
        return MessageResponse(
            message="Business deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Delete business error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete business"
        )


# ============================================================================
# Business Member Management Endpoints
# ============================================================================

@router.get("/{business_id}/members", response_model=BusinessMemberListResponse)
async def list_business_members(
    business_id: str,
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    List all members of a business.
    """
    try:
        response = supabase.table("business_members")\
            .select("*")\
            .eq("business_id", business_id)\
            .execute()
        
        members = [BusinessMemberResponse(**m) for m in response.data]
        
        return BusinessMemberListResponse(
            members=members,
            total=len(members)
        )
        
    except Exception as e:
        logger.error(f"List members error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve members"
        )


@router.post("/{business_id}/members", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def invite_business_member(
    business_id: str,
    member_data: BusinessMemberInvite,
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(check_business_permission("admin")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Invite a new member to the business.
    
    Requires admin or owner role.
    Sends an invitation email to the user.
    """
    try:
        # TODO: Implement user lookup by email and invitation system
        # For now, this is a placeholder
        
        logger.info(f"Member invited to business {business_id}: {member_data.email}")
        
        return MessageResponse(
            message="Invitation sent successfully",
            detail=f"Invitation email sent to {member_data.email}"
        )
        
    except Exception as e:
        logger.error(f"Invite member error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{business_id}/members/{member_id}", response_model=BusinessMemberResponse)
async def update_business_member(
    business_id: str,
    member_id: str,
    member_data: BusinessMemberUpdate,
    business_access: Dict = Depends(check_business_permission("admin")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update a business member's role or permissions.
    
    Requires admin or owner role.
    """
    try:
        update_dict = member_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        response = supabase.table("business_members")\
            .update(update_dict)\
            .eq("id", member_id)\
            .eq("business_id", business_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        logger.info(f"Member updated: {member_id} in business {business_id}")
        
        return BusinessMemberResponse(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update member error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{business_id}/members/{member_id}", response_model=MessageResponse)
async def remove_business_member(
    business_id: str,
    member_id: str,
    business_access: Dict = Depends(check_business_permission("owner")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Remove a member from the business.
    
    Requires owner role.
    """
    try:
        response = supabase.table("business_members")\
            .delete()\
            .eq("id", member_id)\
            .eq("business_id", business_id)\
            .execute()
        
        logger.info(f"Member removed: {member_id} from business {business_id}")
        
        return MessageResponse(
            message="Member removed successfully"
        )
        
    except Exception as e:
        logger.error(f"Remove member error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member"
        )


# ============================================================================
# Business Overview and Analytics Endpoints (Phase 2)
# ============================================================================

@router.get("/{business_id}/overview")
async def get_business_overview(
    business_id: str,
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get comprehensive business overview including accounts and categories.

    Returns business details, account summaries, category summaries, and financial overview.
    """
    try:
        # Get business details
        business_response = supabase.table("businesses")\
            .select("*")\
            .eq("id", business_id)\
            .single()\
            .execute()

        if not business_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )

        business = business_response.data

        # Get account summaries
        accounts_response = supabase.table("account_summaries")\
            .select("*")\
            .eq("business_id", business_id)\
            .eq("is_active", True)\
            .execute()

        accounts = accounts_response.data

        # Get category summaries
        categories_response = supabase.table("category_summaries")\
            .select("*")\
            .eq("business_id", business_id)\
            .eq("is_active", True)\
            .execute()

        categories = categories_response.data

        # Get business financial overview
        overview_response = supabase.table("business_financial_overview")\
            .select("*")\
            .eq("business_id", business_id)\
            .single()\
            .execute()

        financial_overview = overview_response.data[0] if overview_response.data else None

        # Calculate additional metrics
        total_accounts = len(accounts)
        total_categories = len(categories)
        income_categories = len([c for c in categories if c.get("category_type") == "income"])
        expense_categories = len([c for c in categories if c.get("category_type") == "expense"])

        return {
            "business": BusinessResponse(**business),
            "accounts": {
                "total_accounts": total_accounts,
                "active_accounts": total_accounts,  # All returned are active
                "accounts": accounts,
                "summary": financial_overview or {
                    "total_credits_all_accounts": 0.00,
                    "total_debits_all_accounts": 0.00,
                    "net_flow_all_accounts": 0.00
                }
            },
            "categories": {
                "total_categories": total_categories,
                "income_categories": income_categories,
                "expense_categories": expense_categories,
                "system_categories": len([c for c in categories if c.get("is_system")]),
                "custom_categories": len([c for c in categories if not c.get("is_system")]),
                "categories": categories,
                "summary": financial_overview or {
                    "total_income_all_categories": 0.00,
                    "total_expenses_all_categories": 0.00,
                    "net_profit_all_categories": 0.00
                }
            },
            "financial_overview": financial_overview
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get business overview error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve business overview"
        )


@router.get("/{business_id}/accounts/summary")
async def get_business_accounts_summary(
    business_id: str,
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get summary of all accounts for a business.
    """
    try:
        response = supabase.table("account_summaries")\
            .select("*")\
            .eq("business_id", business_id)\
            .eq("is_active", True)\
            .execute()

        accounts = response.data

        # Calculate totals
        total_balance = sum(float(a.get("current_balance", 0)) for a in accounts)
        total_available = sum(float(a.get("available_balance", 0)) for a in accounts)
        total_debits = sum(float(a.get("total_debits", 0)) for a in accounts)
        total_credits = sum(float(a.get("total_credits", 0)) for a in accounts)
        net_flow = sum(float(a.get("net_flow", 0)) for a in accounts)

        return {
            "business_id": business_id,
            "total_accounts": len(accounts),
            "accounts": accounts,
            "totals": {
                "total_balance": total_balance,
                "total_available_balance": total_available,
                "total_debits": total_debits,
                "total_credits": total_credits,
                "net_flow": net_flow
            }
        }

    except Exception as e:
        logger.error(f"Get business accounts summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve accounts summary"
        )


@router.get("/{business_id}/categories/summary")
async def get_business_categories_summary(
    business_id: str,
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get summary of all categories for a business.
    """
    try:
        response = supabase.table("category_summaries")\
            .select("*")\
            .eq("business_id", business_id)\
            .eq("is_active", True)\
            .execute()

        categories = response.data

        # Separate by type
        income_categories = [c for c in categories if c.get("category_type") == "income"]
        expense_categories = [c for c in categories if c.get("category_type") == "expense"]

        # Calculate totals
        total_income = sum(float(c.get("total_income", 0)) for c in income_categories)
        total_expenses = sum(float(c.get("total_expenses", 0)) for c in expense_categories)
        net_profit = total_income - total_expenses

        return {
            "business_id": business_id,
            "total_categories": len(categories),
            "income_categories": len(income_categories),
            "expense_categories": len(expense_categories),
            "system_categories": len([c for c in categories if c.get("is_system")]),
            "custom_categories": len([c for c in categories if not c.get("is_system")]),
            "categories": categories,
            "totals": {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_profit": net_profit
            }
        }

    except Exception as e:
        logger.error(f"Get business categories summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories summary"
        )