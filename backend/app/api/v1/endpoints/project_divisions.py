"""
Project Division management endpoints for creating and managing project divisions.
Handles project division CRUD operations within businesses.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from loguru import logger
from typing import Dict, Any, List
from uuid import UUID

from app.schemas.project_division import (
    ProjectDivisionCreate,
    ProjectDivisionUpdate,
    ProjectDivisionResponse,
    ProjectDivisionListResponse,
    ProjectDivisionWithStats
)
from app.schemas.auth import MessageResponse
from app.core.security import get_current_user
from app.core.deps import Pagination, get_business_access, check_business_permission
from app.db.supabase import get_supabase_client
from app.services.project_division_service import ProjectDivisionService
from supabase import Client

router = APIRouter(prefix="/businesses/{business_id}/divisions", tags=["Project Divisions"])


@router.post("/", response_model=ProjectDivisionResponse, status_code=status.HTTP_201_CREATED)
async def create_division(
    business_id: str,
    division_data: ProjectDivisionCreate,
    business_access: Dict = Depends(check_business_permission("admin")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Create a new project division within a business.

    Requires admin or owner role.
    """
    try:
        # Ensure business_id matches
        if str(division_data.business_id) != business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business ID mismatch"
            )

        service = ProjectDivisionService(supabase)
        division = await service.create_division(division_data)

        logger.info(f"Project division created: {division.id} in business {business_id}")

        return division

    except ValueError as e:
        logger.error(f"Create division validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create division error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=ProjectDivisionListResponse)
async def list_divisions(
    business_id: str,
    pagination: Pagination = Depends(),
    include_inactive: bool = Query(False, description="Include inactive divisions"),
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    List all project divisions for a business.

    Returns paginated list of divisions.
    """
    try:
        service = ProjectDivisionService(supabase)
        divisions = await service.list_divisions(business_id, include_inactive)

        # Apply pagination
        start_idx = pagination.offset
        end_idx = start_idx + pagination.limit
        paginated_divisions = divisions[start_idx:end_idx]

        total = len(divisions)
        metadata = pagination.get_pagination_metadata(total)

        return ProjectDivisionListResponse(
            divisions=paginated_divisions,
            total=total,
            page=metadata["page"],
            page_size=metadata["page_size"],
            total_pages=metadata["total_pages"]
        )

    except Exception as e:
        logger.error(f"List divisions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve divisions"
        )


@router.get("/{division_id}", response_model=ProjectDivisionWithStats)
async def get_division(
    business_id: str,
    division_id: str,
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get detailed information about a specific project division.

    Includes division details and statistics.
    """
    try:
        service = ProjectDivisionService(supabase)
        division = await service.get_division_with_stats(division_id, business_id)

        return division

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project division not found"
        )
    except Exception as e:
        logger.error(f"Get division error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve division"
        )


@router.patch("/{division_id}", response_model=ProjectDivisionResponse)
async def update_division(
    business_id: str,
    division_id: str,
    division_data: ProjectDivisionUpdate,
    business_access: Dict = Depends(check_business_permission("admin")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update project division information.

    Requires admin or owner role.
    """
    try:
        service = ProjectDivisionService(supabase)
        division = await service.update_division(division_id, business_id, division_data)

        logger.info(f"Project division updated: {division_id} in business {business_id}")

        return division

    except ValueError as e:
        logger.error(f"Update division validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update division error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{division_id}", response_model=MessageResponse)
async def delete_division(
    business_id: str,
    division_id: str,
    business_access: Dict = Depends(check_business_permission("owner")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Delete a project division.

    Requires owner role. Division must not have any transactions or documents.
    """
    try:
        service = ProjectDivisionService(supabase)
        await service.delete_division(division_id, business_id)

        logger.info(f"Project division deleted: {division_id} from business {business_id}")

        return MessageResponse(
            message="Project division deleted successfully"
        )

    except ValueError as e:
        logger.error(f"Delete division validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Delete division error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete division"
        )


# ============================================================================
# Project Division Analytics Endpoints
# ============================================================================

@router.get("/{division_id}/stats")
async def get_division_stats(
    business_id: str,
    division_id: str,
    business_access: Dict = Depends(get_business_access),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get detailed statistics for a project division.

    Includes transaction counts, amounts, and document counts.
    """
    try:
        service = ProjectDivisionService(supabase)
        division = await service.get_division_with_stats(division_id, business_id)

        return {
            "division": division,
            "summary": {
                "transaction_count": division.transaction_count,
                "document_count": division.document_count,
                "total_amount": division.total_amount
            }
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project division not found"
        )
    except Exception as e:
        logger.error(f"Get division stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve division statistics"
        )