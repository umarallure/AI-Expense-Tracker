"""
Transaction/Expense management endpoints for creating and managing financial transactions.
Handles transaction CRUD operations.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from loguru import logger
from typing import Dict, Any, List
from uuid import uuid4, UUID
from datetime import datetime
from decimal import Decimal

from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    Transaction,
    TransactionList,
    TransactionApproval,
    TransactionApprovalUpdate
)
from app.schemas.auth import MessageResponse
from app.core.security import get_current_user
from app.core.deps import get_business_access, check_business_permission
from app.db.supabase import get_supabase_client
from supabase import Client
from app.services.ledger_service import ledger_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(check_business_permission("member")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Create a new transaction/expense.

    Requires member or higher role.
    """
    try:
        business_id = transaction_data.business_id

        # Generate UUID for the transaction
        transaction_id = str(uuid4())

        # Prepare transaction data
        transaction_dict = transaction_data.model_dump()
        
        # Convert UUID objects, datetime objects, and enums to strings for Supabase
        for key in transaction_dict:
            if isinstance(transaction_dict[key], UUID):
                transaction_dict[key] = str(transaction_dict[key])
            elif isinstance(transaction_dict[key], datetime):
                transaction_dict[key] = transaction_dict[key].isoformat()
            elif hasattr(transaction_dict[key], 'value'):  # Enum objects
                transaction_dict[key] = transaction_dict[key].value
        
        transaction_dict["id"] = transaction_id
        transaction_dict["user_id"] = str(current_user["user_id"])
        transaction_dict["created_at"] = datetime.utcnow().isoformat()
        transaction_dict["updated_at"] = datetime.utcnow().isoformat()

        # Insert into Supabase
        result = supabase.table("transactions").insert(transaction_dict).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create transaction"
            )

        created_transaction = result.data[0]

        # Create ledger entry if transaction is approved and affects account balance
        if created_transaction.get("status") == "approved":
            try:
                # Determine transaction type and change amount
                is_income = created_transaction.get("is_income", False)
                transaction_amount = Decimal(str(created_transaction["amount"]))

                # For income: add to balance (positive change)
                # For expense: subtract from balance (negative change)
                change_amount = transaction_amount if is_income else -transaction_amount
                transaction_type = "income" if is_income else "expense"

                logger.info(f"Creating ledger entry for transaction {transaction_id}: is_income={is_income}, amount={transaction_amount}, change_amount={change_amount}")

                # Create ledger entry and update account balance
                await ledger_service.create_ledger_entry(
                    supabase=supabase,
                    business_id=str(business_id),
                    account_id=created_transaction["account_id"],
                    transaction_id=transaction_id,
                    change_amount=change_amount,
                    transaction_type=transaction_type,
                    user_id=str(current_user["user_id"]),
                    description=f"Direct transaction creation: {created_transaction['description']}"
                )

                logger.info(f"Ledger entry created successfully for transaction {transaction_id}")

            except Exception as ledger_error:
                logger.error(f"Failed to create ledger entry for transaction {transaction_id}: {ledger_error}")
                # For now, don't fail the transaction creation if ledger fails
                # TODO: Consider whether to fail transaction creation on ledger failure

        return Transaction(**created_transaction)

    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}"
        )


@router.get("/", response_model=TransactionList)
async def get_transactions(
    business_id: str = Query(..., description="Business ID to filter transactions"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(check_business_permission("member")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get transactions for a business.

    Requires member or higher role.
    """
    try:
        # Query transactions for the business
        query = supabase.table("transactions").select("*").eq("business_id", business_id)
        result = query.range(skip, skip + limit - 1).execute()

        # Get total count
        count_result = supabase.table("transactions").select("*", count="exact").eq("business_id", business_id).execute()
        total = count_result.count

        transactions = [Transaction(**item) for item in result.data]

        return TransactionList(transactions=transactions, total=total)

    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transactions: {str(e)}"
        )


@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(
    transaction_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(check_business_permission("member")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get a specific transaction by ID.

    Requires member or higher role.
    """
    try:
        result = supabase.table("transactions").select("*").eq("id", transaction_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        transaction = result.data[0]

        # Check if user has access to this business (manual check since business_id not in path)
        business_response = supabase.table("business_members").select("*").eq(
            "business_id", transaction["business_id"]
        ).eq("user_id", current_user["user_id"]).eq("status", "active").execute()
        
        if not business_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this transaction"
            )

        return Transaction(**transaction)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transaction: {str(e)}"
        )


@router.put("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: str,
    transaction_data: TransactionUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update a transaction.

    Users can edit their own transactions if not approved.
    Admins can edit any transaction.
    """
    try:
        # Check if transaction exists
        existing = supabase.table("transactions").select("*").eq("id", transaction_id).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        transaction = existing.data[0]
        business_id = transaction["business_id"]

        # Check business access
        business_response = supabase.table("business_members").select("*").eq(
            "business_id", business_id
        ).eq("user_id", current_user["user_id"]).eq("status", "active").execute()
        
        if not business_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this business"
            )
        
        member = business_response.data[0]
        user_role = member.get("role", "viewer")

        user_id = str(current_user["user_id"])
        transaction_user_id = transaction.get("user_id")
        transaction_status = transaction.get("status")

        # Allow editing if:
        # 1. User is admin/owner, OR
        # 2. User created the transaction AND it's not approved
        can_edit = (
            user_role in ["admin", "owner"] or
            (transaction_user_id == user_id and transaction_status != "approved")
        )

        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own pending transactions, or you need admin permissions"
            )

        # Update transaction
        update_dict = transaction_data.model_dump(exclude_unset=True)
        
        # Convert UUID objects to strings for Supabase
        if "business_id" in update_dict:
            update_dict["business_id"] = str(update_dict["business_id"])
        if "account_id" in update_dict:
            update_dict["account_id"] = str(update_dict["account_id"])
        if "category_id" in update_dict and update_dict["category_id"]:
            update_dict["category_id"] = str(update_dict["category_id"])
        if "user_id" in update_dict and update_dict["user_id"]:
            update_dict["user_id"] = str(update_dict["user_id"])
        
        update_dict["updated_at"] = datetime.utcnow().isoformat()

        result = supabase.table("transactions").update(update_dict).eq("id", transaction_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update transaction"
            )

        return Transaction(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update transaction: {str(e)}"
        )


@router.delete("/{transaction_id}", response_model=MessageResponse)
async def delete_transaction(
    transaction_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Delete a transaction.

    Users can delete their own transactions if not approved.
    Admins can delete any transaction.
    """
    try:
        # Check if transaction exists
        existing = supabase.table("transactions").select("*").eq("id", transaction_id).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        transaction = existing.data[0]
        business_id = transaction["business_id"]

        # Check business access
        business_response = supabase.table("business_members").select("*").eq(
            "business_id", business_id
        ).eq("user_id", current_user["user_id"]).eq("status", "active").execute()
        
        if not business_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this business"
            )
        
        member = business_response.data[0]
        user_role = member.get("role", "viewer")

        user_id = str(current_user["user_id"])
        transaction_user_id = transaction.get("user_id")
        transaction_status = transaction.get("status")

        # Allow deletion only for pending and draft transactions
        # Either admins/owners can delete them, or the user who created them
        can_delete = (
            transaction_status in ["pending", "draft"] and
            (user_role in ["admin", "owner"] or transaction_user_id == user_id)
        )

        if not can_delete:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only pending and draft transactions can be deleted, and you must be an admin or the transaction creator"
            )

        # Delete transaction
        supabase.table("transactions").delete().eq("id", transaction_id).execute()

        return MessageResponse(message="Transaction deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete transaction: {str(e)}"
        )


@router.post("/{transaction_id}/approve", response_model=Transaction)
async def approve_transaction(
    transaction_id: str,
    approval_data: TransactionApproval,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Approve or reject a transaction.

    Requires admin or owner role.
    """
    try:
        # Check if transaction exists
        existing = supabase.table("transactions").select("*").eq("id", transaction_id).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        transaction = existing.data[0]
        business_id = transaction["business_id"]

        # Check business access and admin permissions
        business_response = supabase.table("business_members").select("*").eq(
            "business_id", business_id
        ).eq("user_id", current_user["user_id"]).eq("status", "active").execute()
        
        if not business_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this business"
            )
        
        member = business_response.data[0]
        user_role = member.get("role", "viewer")
        
        if user_role not in ["admin", "owner"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin permissions required to approve transactions"
            )

        # Update transaction with approval
        update_dict = {
            "status": approval_data.status.value,
            "approved_by": str(current_user["user_id"]),
            "approved_at": datetime.utcnow().isoformat(),
            "approval_notes": approval_data.approval_notes,
            "updated_at": datetime.utcnow().isoformat()
        }

        result = supabase.table("transactions").update(update_dict).eq("id", transaction_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update transaction approval"
            )

        updated_transaction = result.data[0]

        # Create ledger entry if transaction is approved and affects account balance
        if approval_data.status.value == "approved":
            try:
                # Determine transaction type and change amount
                is_income = updated_transaction.get("is_income", False)
                transaction_amount = Decimal(str(updated_transaction["amount"]))

                # For income: add to balance (positive change)
                # For expense: subtract from balance (negative change)
                change_amount = transaction_amount if is_income else -transaction_amount
                transaction_type = "income" if is_income else "expense"

                # Create ledger entry and update account balance
                await ledger_service.create_ledger_entry(
                    supabase=supabase,
                    business_id=str(business_id),
                    account_id=updated_transaction["account_id"],
                    transaction_id=transaction_id,
                    change_amount=change_amount,
                    transaction_type=transaction_type,
                    user_id=str(current_user["user_id"]),
                    description=f"Transaction approval: {updated_transaction['description']}"
                )

                logger.info(f"Ledger entry created for approved transaction {transaction_id}")

            except Exception as ledger_error:
                logger.error(f"Failed to create ledger entry for transaction {transaction_id}: {ledger_error}")
                # Don't fail the approval if ledger creation fails, but log it

        return Transaction(**updated_transaction)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve transaction: {str(e)}"
        )


@router.put("/{transaction_id}/approve-edit", response_model=Transaction)
async def approve_and_edit_transaction(
    transaction_id: str,
    approval_data: TransactionApprovalUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Approve/reject a transaction with optional edits.

    Requires admin or owner role.
    """
    try:
        # Check if transaction exists
        existing = supabase.table("transactions").select("*").eq("id", transaction_id).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        transaction = existing.data[0]
        business_id = transaction["business_id"]

        # Check business access and admin permissions
        business_response = supabase.table("business_members").select("*").eq(
            "business_id", business_id
        ).eq("user_id", current_user["user_id"]).eq("status", "active").execute()
        
        if not business_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this business"
            )
        
        member = business_response.data[0]
        user_role = member.get("role", "viewer")
        
        if user_role not in ["admin", "owner"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin permissions required to approve transactions"
            )

        # Prepare update data
        update_dict = approval_data.model_dump(exclude_unset=True)
        
        # Convert UUID objects and datetime to strings for Supabase
        for key in update_dict:
            if isinstance(update_dict[key], UUID):
                update_dict[key] = str(update_dict[key])
            elif isinstance(update_dict[key], datetime):
                update_dict[key] = update_dict[key].isoformat()
            elif hasattr(update_dict[key], 'value'):  # Enum objects
                update_dict[key] = update_dict[key].value

        # Add approval metadata
        update_dict["approved_by"] = str(current_user["user_id"])
        update_dict["approved_at"] = datetime.utcnow().isoformat()
        update_dict["updated_at"] = datetime.utcnow().isoformat()

        result = supabase.table("transactions").update(update_dict).eq("id", transaction_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update transaction"
            )

        updated_transaction = result.data[0]

        # Create ledger entry if transaction is approved and affects account balance
        if approval_data.status.value == "approved":
            try:
                # Determine transaction type and change amount
                is_income = updated_transaction.get("is_income", False)
                transaction_amount = Decimal(str(updated_transaction["amount"]))

                # For income: add to balance (positive change)
                # For expense: subtract from balance (negative change)
                change_amount = transaction_amount if is_income else -transaction_amount
                transaction_type = "income" if is_income else "expense"

                # Create ledger entry and update account balance
                await ledger_service.create_ledger_entry(
                    supabase=supabase,
                    business_id=str(business_id),
                    account_id=updated_transaction["account_id"],
                    transaction_id=transaction_id,
                    change_amount=change_amount,
                    transaction_type=transaction_type,
                    user_id=str(current_user["user_id"]),
                    description=f"Transaction approval with edits: {updated_transaction['description']}"
                )

                logger.info(f"Ledger entry created for approved transaction {transaction_id}")

            except Exception as ledger_error:
                logger.error(f"Failed to create ledger entry for transaction {transaction_id}: {ledger_error}")
                # Don't fail the approval if ledger creation fails, but log it

        return Transaction(**updated_transaction)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving and editing transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve and edit transaction: {str(e)}"
        )


@router.get("/pending/{business_id}", response_model=TransactionList)
async def get_pending_transactions(
    business_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(check_business_permission("accountant")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get pending transactions for approval.

    Requires accountant or higher role.
    """
    try:
        # business_access already validates admin access to this business

        # Query pending transactions for the business
        query = supabase.table("transactions").select("*").eq("business_id", business_id).eq("status", "pending")
        result = query.range(skip, skip + limit - 1).execute()

        # Get total count
        count_result = supabase.table("transactions").select("*", count="exact").eq("business_id", business_id).eq("status", "pending").execute()
        total = count_result.count

        transactions = [Transaction(**item) for item in result.data]

        return TransactionList(transactions=transactions, total=total)

    except Exception as e:
        logger.error(f"Error fetching pending transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pending transactions: {str(e)}"
        )