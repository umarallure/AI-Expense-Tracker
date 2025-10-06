"""
Category management endpoints for creating and managing transaction categories.
Handles category CRUD operations and hierarchical management.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from loguru import logger
from typing import Dict, Any, List

from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
    CategorySummary,
    CategoryTreeNode,
    CategoryHierarchy
)
from app.schemas.auth import MessageResponse
from app.core.security import get_current_user
from app.core.deps import Pagination, get_business_access, check_business_permission
from app.db.supabase import get_supabase_client
from supabase import Client

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(check_business_permission("admin")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Create a new category for a business.

    Requires admin or owner role.
    """
    try:
        business_id = category_data.business_id

        # Convert Pydantic model to dict
        category_dict = category_data.model_dump()

        response = supabase.table("categories").insert(category_dict).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create category"
            )

        category = response.data[0]
        logger.info(f"Category created: {category['id']} for business {business_id}")

        return CategoryResponse(**category)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create category error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=CategoryListResponse)
async def list_categories(
    business_id: str = Query(..., description="Business ID to filter categories"),
    category_type: str = Query(None, description="Filter by category type (income/expense)"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    include_system: bool = Query(True, description="Include system categories"),
    pagination: Pagination = Depends(),
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    List all categories for a business.

    Supports filtering by type and includes options for system/inactive categories.
    """
    try:
        # Build query
        query = supabase.table("categories").select("*", count="exact").eq("business_id", business_id)

        if not include_inactive:
            query = query.eq("is_active", True)

        if not include_system:
            query = query.eq("is_system", False)

        if category_type:
            query = query.eq("category_type", category_type)

        # Order by display_order, then by name
        query = query.order("display_order").order("category_name")

        # Apply pagination
        response = query.range(
            pagination.offset,
            pagination.offset + pagination.limit - 1
        ).execute()

        categories = [CategoryResponse(**c) for c in response.data]
        total = response.count or 0

        metadata = pagination.get_pagination_metadata(total)

        return CategoryListResponse(
            categories=categories,
            total=total,
            page=metadata["page"],
            page_size=metadata["page_size"],
            total_pages=metadata["total_pages"]
        )

    except Exception as e:
        logger.error(f"List categories error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories"
        )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get detailed information about a specific category.
    """
    try:
        response = supabase.table("categories")\
            .select("*")\
            .eq("id", category_id)\
            .single()\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        return CategoryResponse(**response.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get category error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category"
        )


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    business_access: Dict = Depends(check_business_permission("admin")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update category information.

    Requires admin or owner role. System categories can only be updated by owners.
    """
    try:
        # Check if this is a system category
        category_response = supabase.table("categories")\
            .select("is_system, business_id")\
            .eq("id", category_id)\
            .single()\
            .execute()

        if not category_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        category = category_response.data

        # If it's a system category, only owners can update
        if category["is_system"] and business_access.get("role") != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only business owners can modify system categories"
            )

        # Convert Pydantic model to dict
        update_dict = category_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        response = supabase.table("categories")\
            .update(update_dict)\
            .eq("id", category_id)\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        logger.info(f"Category updated: {category_id}")

        return CategoryResponse(**response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update category error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_category(
    category_id: str,
    business_access: Dict = Depends(check_business_permission("owner")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Delete a category.

    Requires owner role. System categories cannot be deleted.
    """
    try:
        # Check if this is a system category
        category_response = supabase.table("categories")\
            .select("is_system, category_name")\
            .eq("id", category_id)\
            .single()\
            .execute()

        if not category_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        category = category_response.data

        if category["is_system"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System categories cannot be deleted"
            )

        response = supabase.table("categories")\
            .delete()\
            .eq("id", category_id)\
            .execute()

        logger.info(f"Category deleted: {category_id}")

        return MessageResponse(
            message="Category deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete category error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category"
        )


@router.get("/hierarchy/business/{business_id}", response_model=CategoryHierarchy)
async def get_category_hierarchy(
    business_id: str,
    include_inactive: bool = Query(False, description="Include inactive categories"),
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get hierarchical structure of categories for a business.

    Returns categories organized in a tree structure.
    """
    try:
        # Get all categories
        query = supabase.table("categories")\
            .select("*")\
            .eq("business_id", business_id)

        if not include_inactive:
            query = query.eq("is_active", True)

        query = query.order("display_order").order("category_name")

        response = query.execute()

        categories = response.data

        # Build hierarchy
        category_map = {c["id"]: c for c in categories}
        root_categories = []

        for category in categories:
            if category["parent_id"] is None:
                # Root category
                root_node = CategoryTreeNode(**category)
                root_categories.append(root_node)
            else:
                # Child category - add to parent
                parent = category_map.get(category["parent_id"])
                if parent:
                    if not hasattr(parent, 'children'):
                        parent.children = []
                    parent.children.append(CategoryTreeNode(**category))

        return CategoryHierarchy(
            root_categories=root_categories,
            total_categories=len(categories)
        )

    except Exception as e:
        logger.error(f"Get category hierarchy error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category hierarchy"
        )


@router.get("/summary/business/{business_id}")
async def get_categories_summary(
    business_id: str,
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get summary of all categories for a business.

    Returns category statistics and transaction totals.
    """
    try:
        # Use the category_summaries view
        response = supabase.table("category_summaries")\
            .select("*")\
            .eq("business_id", business_id)\
            .eq("is_active", True)\
            .execute()

        categories = [CategorySummary(**c) for c in response.data]

        # Calculate totals
        income_categories = [c for c in categories if c.category_type.value == "income"]
        expense_categories = [c for c in categories if c.category_type.value == "expense"]

        total_income = sum(float(c.total_income) for c in income_categories)
        total_expenses = sum(float(c.total_expenses) for c in expense_categories)
        net_amount = total_income - total_expenses

        return {
            "categories": categories,
            "summary": {
                "total_categories": len(categories),
                "income_categories": len(income_categories),
                "expense_categories": len(expense_categories),
                "system_categories": len([c for c in categories if c.is_system]),
                "custom_categories": len([c for c in categories if not c.is_system]),
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_amount": net_amount
            }
        }

    except Exception as e:
        logger.error(f"Get categories summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories summary"
        )