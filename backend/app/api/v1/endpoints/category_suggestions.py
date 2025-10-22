"""
Category Suggestion API endpoints.
Provides intelligent category suggestions for transactions using AI analysis.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query, Body
from loguru import logger
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.services.category_suggestion_service import CategorySuggestionService
from app.schemas.auth import MessageResponse
from app.core.security import get_current_user
from app.core.deps import get_business_access
from app.db.supabase import get_supabase_client
from supabase import Client

router = APIRouter(prefix="/category-suggestions", tags=["Category Suggestions"])


class CategorySuggestionRequest(BaseModel):
    """Request model for category suggestions."""
    transaction_ids: Optional[List[str]] = None
    include_uncategorized_only: bool = True
    max_suggestions: int = 50


class CategorySuggestionResponse(BaseModel):
    """Response model for category suggestions."""
    transaction_id: str
    suggested_category_id: str
    suggested_category_name: str
    confidence_score: float
    reason: str
    suggestion_type: str  # "historical_pattern", "ai_analysis", "keyword_match"


class BulkSuggestionResponse(BaseModel):
    """Response model for bulk category suggestions."""
    suggestions: List[CategorySuggestionResponse]
    total_suggestions: int
    processing_time_seconds: float


class SingleSuggestionRequest(BaseModel):
    """Request model for single transaction suggestion."""
    description: str
    vendor: Optional[str] = None
    amount: float
    is_income: bool = False


@router.post("/bulk", response_model=BulkSuggestionResponse)
async def get_bulk_category_suggestions(
    request: CategorySuggestionRequest,
    business_id: str = Query(..., description="Business ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get category suggestions for multiple transactions.

    Analyzes transaction patterns and provides intelligent category suggestions
    with confidence scores.
    """
    import time
    start_time = time.time()

    try:
        suggestion_service = CategorySuggestionService()

        # Get transactions to analyze
        query = supabase.table("transactions").select(
            "id, description, vendor, amount, is_income, category_id"
        ).eq("business_id", business_id)

        if request.include_uncategorized_only:
            query = query.is_("category_id", None)

        if request.transaction_ids:
            query = query.in_("id", request.transaction_ids)

        query = query.limit(request.max_suggestions)

        response = query.execute()

        if not response.data:
            return BulkSuggestionResponse(
                suggestions=[],
                total_suggestions=0,
                processing_time_seconds=time.time() - start_time
            )

        transactions = response.data

        # Get suggestions
        suggestions_data = await suggestion_service.suggest_categories(
            transactions=transactions,
            business_id=business_id,
            supabase_client=supabase
        )

        # Convert to response format
        suggestions = [
            CategorySuggestionResponse(**suggestion)
            for suggestion in suggestions_data
        ]

        processing_time = time.time() - start_time

        logger.info(
            f"Generated {len(suggestions)} category suggestions for business {business_id} "
            f"in {processing_time:.2f}s"
        )

        return BulkSuggestionResponse(
            suggestions=suggestions,
            total_suggestions=len(suggestions),
            processing_time_seconds=processing_time
        )

    except Exception as e:
        logger.error(f"Bulk category suggestions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate category suggestions"
        )


@router.post("/single", response_model=Optional[CategorySuggestionResponse])
async def get_single_category_suggestion(
    request: SingleSuggestionRequest,
    business_id: str = Query(..., description="Business ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get category suggestion for a single transaction.

    Useful for real-time suggestions during transaction creation or editing.
    """
    try:
        suggestion_service = CategorySuggestionService()

        # Create transaction-like object for analysis
        transaction_data = {
            "description": request.description,
            "vendor": request.vendor,
            "amount": request.amount,
            "is_income": request.is_income
        }

        suggestion = await suggestion_service.suggest_category_for_transaction(
            transaction=transaction_data,
            business_id=business_id,
            supabase_client=supabase
        )

        if suggestion:
            return CategorySuggestionResponse(**suggestion)

        return None

    except Exception as e:
        logger.error(f"Single category suggestion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate category suggestion"
        )


@router.post("/apply/{transaction_id}", response_model=MessageResponse)
async def apply_category_suggestion(
    transaction_id: str,
    category_id: str = Body(..., embed=True),
    business_id: str = Query(..., description="Business ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Apply a category suggestion to a transaction.

    Updates the transaction with the suggested category and learns from the correction.
    """
    try:
        # Update transaction with new category
        update_response = supabase.table("transactions").update({
            "category_id": category_id
        }).eq("id", transaction_id).eq("business_id", business_id).execute()

        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        # Learn from this correction for future suggestions
        suggestion_service = CategorySuggestionService()
        await suggestion_service.learn_from_correction(
            transaction_id=transaction_id,
            corrected_category_id=category_id,
            business_id=business_id,
            supabase_client=supabase
        )

        logger.info(
            f"Applied category {category_id} to transaction {transaction_id} "
            f"for business {business_id}"
        )

        return MessageResponse(
            message="Category suggestion applied successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apply category suggestion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply category suggestion"
        )


@router.get("/stats/{business_id}")
async def get_suggestion_stats(
    business_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get statistics about category suggestions for a business.

    Shows how many transactions are uncategorized and suggestion effectiveness.
    """
    try:
        # Get total transactions
        total_response = supabase.table("transactions").select(
            "id", count="exact"
        ).eq("business_id", business_id).execute()

        # Get uncategorized transactions
        uncategorized_response = supabase.table("transactions").select(
            "id", count="exact"
        ).eq("business_id", business_id).is_("category_id", None).execute()

        # Get categorized transactions by suggestion type (if we stored this info)
        # For now, just return basic stats

        return {
            "total_transactions": total_response.count or 0,
            "uncategorized_transactions": uncategorized_response.count or 0,
            "categorized_transactions": (total_response.count or 0) - (uncategorized_response.count or 0),
            "categorization_rate": round(
                ((total_response.count or 0) - (uncategorized_response.count or 0)) /
                max(total_response.count or 1, 1) * 100,
                1
            )
        }

    except Exception as e:
        logger.error(f"Get suggestion stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve suggestion statistics"
        )