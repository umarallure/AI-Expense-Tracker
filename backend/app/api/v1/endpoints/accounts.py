"""
Account management endpoints for creating and managing financial accounts.
Handles account CRUD operations and balance management.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from loguru import logger
from typing import Dict, Any, List
from decimal import Decimal

from app.schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountListResponse,
    AccountSummary,
    AccountBalanceUpdate
)
from app.schemas.auth import MessageResponse
from app.core.security import get_current_user
from app.core.deps import Pagination, get_business_access, check_business_permission
from app.db.supabase import get_supabase_client
from supabase import Client

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(check_business_permission("admin")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Create a new account for a business.

    Requires admin or owner role.
    """
    try:
        business_id = account_data.business_id

        # Convert Pydantic model to dict and handle Decimal types
        account_dict = account_data.model_dump()
        account_dict["current_balance"] = float(account_dict["current_balance"])
        if account_dict.get("available_balance") is not None:
            account_dict["available_balance"] = float(account_dict["available_balance"])
        if account_dict.get("credit_limit") is not None:
            account_dict["credit_limit"] = float(account_dict["credit_limit"])
        if account_dict.get("interest_rate") is not None:
            account_dict["interest_rate"] = float(account_dict["interest_rate"])
        if account_dict.get("minimum_payment") is not None:
            account_dict["minimum_payment"] = float(account_dict["minimum_payment"])

        response = supabase.table("accounts").insert(account_dict).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create account"
            )

        account = response.data[0]
        logger.info(f"Account created: {account['id']} for business {business_id}")

        return AccountResponse(**account)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create account error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=AccountListResponse)
async def list_accounts(
    business_id: str = Query(..., description="Business ID to filter accounts"),
    include_inactive: bool = Query(False, description="Include inactive accounts"),
    pagination: Pagination = Depends(),
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    List all accounts for a business.

    Returns active accounts by default, optionally includes inactive ones.
    """
    try:
        # Build query
        query = supabase.table("accounts").select("*", count="exact").eq("business_id", business_id)

        if not include_inactive:
            query = query.eq("is_active", True)

        # Apply pagination
        response = query.range(
            pagination.offset,
            pagination.offset + pagination.limit - 1
        ).execute()

        accounts = [AccountResponse(**a) for a in response.data]
        total = response.count or 0

        metadata = pagination.get_pagination_metadata(total)

        return AccountListResponse(
            accounts=accounts,
            total=total,
            page=metadata["page"],
            page_size=metadata["page_size"],
            total_pages=metadata["total_pages"]
        )

    except Exception as e:
        logger.error(f"List accounts error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve accounts"
        )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get detailed information about a specific account.
    """
    try:
        response = supabase.table("accounts")\
            .select("*")\
            .eq("id", account_id)\
            .single()\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        return AccountResponse(**response.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get account error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve account"
        )


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account_data: AccountUpdate,
    business_access: Dict = Depends(check_business_permission("admin")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update account information.

    Requires admin or owner role.
    """
    try:
        # Convert Pydantic model to dict and handle Decimal types
        update_dict = account_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Convert Decimal fields to float for Supabase
        decimal_fields = ['current_balance', 'available_balance', 'credit_limit', 'interest_rate', 'minimum_payment']
        for field in decimal_fields:
            if field in update_dict and update_dict[field] is not None:
                update_dict[field] = float(update_dict[field])

        response = supabase.table("accounts")\
            .update(update_dict)\
            .eq("id", account_id)\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        logger.info(f"Account updated: {account_id}")

        return AccountResponse(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update account error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{account_id}", response_model=MessageResponse)
async def delete_account(
    account_id: str,
    business_access: Dict = Depends(check_business_permission("owner")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Delete an account.

    Requires owner role. This will cascade delete related transactions.
    """
    try:
        response = supabase.table("accounts")\
            .delete()\
            .eq("id", account_id)\
            .execute()

        logger.info(f"Account deleted: {account_id}")

        return MessageResponse(
            message="Account deleted successfully"
        )

    except Exception as e:
        logger.error(f"Delete account error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


@router.patch("/{account_id}/balance", response_model=AccountResponse)
async def update_account_balance(
    account_id: str,
    balance_data: AccountBalanceUpdate,
    business_access: Dict = Depends(check_business_permission("admin")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update account balance.

    Requires admin or owner role.
    """
    try:
        update_dict = {
            "current_balance": float(balance_data.current_balance)
        }

        if balance_data.available_balance is not None:
            update_dict["available_balance"] = float(balance_data.available_balance)

        response = supabase.table("accounts")\
            .update(update_dict)\
            .eq("id", account_id)\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        logger.info(f"Account balance updated: {account_id}")

        return AccountResponse(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update account balance error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/summary/business/{business_id}")
async def get_accounts_summary(
    business_id: str,
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get summary of all accounts for a business.

    Returns account statistics and totals.
    """
    try:
        # Use the account_summaries view
        response = supabase.table("account_summaries")\
            .select("*")\
            .eq("business_id", business_id)\
            .eq("is_active", True)\
            .execute()

        accounts = [AccountSummary(**a) for a in response.data]

        # Calculate totals
        total_balance = sum(float(a.current_balance) for a in accounts)
        total_available = sum(float(a.available_balance) for a in accounts)
        total_debits = sum(float(a.total_debits) for a in accounts)
        total_credits = sum(float(a.total_credits) for a in accounts)
        net_flow = sum(float(a.net_flow) for a in accounts)

        return {
            "accounts": accounts,
            "summary": {
                "total_accounts": len(accounts),
                "total_balance": total_balance,
                "total_available_balance": total_available,
                "total_debits": total_debits,
                "total_credits": total_credits,
                "net_flow": net_flow
            }
        }

    except Exception as e:
        logger.error(f"Get accounts summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve accounts summary"
        )