"""
Project Division management service.
Handles business logic for project division operations.
"""
from typing import List, Dict, Any, Optional
from app.schemas.project_division import (
    ProjectDivisionCreate,
    ProjectDivisionUpdate,
    ProjectDivisionResponse,
    ProjectDivisionWithStats
)
from app.db.supabase import get_supabase_client
from supabase import Client


class ProjectDivisionService:
    """Service class for project division management operations."""

    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize project division service.

        Args:
            supabase_client: Optional Supabase client, creates new one if not provided
        """
        self.supabase = supabase_client or get_supabase_client()

    async def create_division(self, division_data: ProjectDivisionCreate) -> ProjectDivisionResponse:
        """
        Create a new project division with validation.

        Args:
            division_data: Project division creation data

        Returns:
            Created project division response

        Raises:
            ValueError: If validation fails
        """
        # Validate business exists and user has access
        await self._validate_business_access(division_data.business_id)

        # Check for duplicate division names within business
        await self._validate_unique_division_name(
            division_data.business_id,
            division_data.name
        )

        # Convert to dict
        division_dict = division_data.model_dump()

        # Insert division
        response = self.supabase.table("project_divisions").insert(division_dict).execute()

        if not response.data:
            raise ValueError("Failed to create project division")

        return ProjectDivisionResponse(**response.data[0])

    async def get_division(self, division_id: str, business_id: str) -> ProjectDivisionResponse:
        """
        Get a project division by ID.

        Args:
            division_id: Project division ID
            business_id: Business ID for access validation

        Returns:
            Project division response

        Raises:
            ValueError: If division not found
        """
        # Validate business access
        await self._validate_business_access(business_id)

        response = self.supabase.table("project_divisions")\
            .select("*")\
            .eq("id", division_id)\
            .eq("business_id", business_id)\
            .single()\
            .execute()

        if not response.data:
            raise ValueError("Project division not found")

        return ProjectDivisionResponse(**response.data)

    async def list_divisions(
        self,
        business_id: str,
        include_inactive: bool = False
    ) -> List[ProjectDivisionResponse]:
        """
        List all project divisions for a business.

        Args:
            business_id: Business ID
            include_inactive: Whether to include inactive divisions

        Returns:
            List of project division responses
        """
        # Validate business access
        await self._validate_business_access(business_id)

        query = self.supabase.table("project_divisions")\
            .select("*")\
            .eq("business_id", business_id)

        if not include_inactive:
            query = query.eq("is_active", True)

        response = query.order("name").execute()

        return [ProjectDivisionResponse(**division) for division in response.data]

    async def update_division(
        self,
        division_id: str,
        business_id: str,
        division_data: ProjectDivisionUpdate
    ) -> ProjectDivisionResponse:
        """
        Update a project division.

        Args:
            division_id: Project division ID
            business_id: Business ID
            division_data: Update data

        Returns:
            Updated project division response

        Raises:
            ValueError: If validation fails
        """
        # Validate business access
        await self._validate_business_access(business_id)

        # Check for duplicate names if name is being updated
        if division_data.name is not None:
            await self._validate_unique_division_name(
                business_id,
                division_data.name,
                exclude_id=division_id
            )

        update_dict = division_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise ValueError("No fields to update")

        response = self.supabase.table("project_divisions")\
            .update(update_dict)\
            .eq("id", division_id)\
            .eq("business_id", business_id)\
            .execute()

        if not response.data:
            raise ValueError("Project division not found")

        return ProjectDivisionResponse(**response.data[0])

    async def delete_division(self, division_id: str, business_id: str) -> None:
        """
        Delete a project division.

        Args:
            division_id: Project division ID
            business_id: Business ID

        Raises:
            ValueError: If division has dependent data or not found
        """
        # Validate business access
        await self._validate_business_access(business_id)

        # Check if division has transactions or documents
        await self._validate_no_dependencies(division_id, business_id)

        response = self.supabase.table("project_divisions")\
            .delete()\
            .eq("id", division_id)\
            .eq("business_id", business_id)\
            .execute()

        if not response.data:
            raise ValueError("Project division not found")

    async def get_division_with_stats(
        self,
        division_id: str,
        business_id: str
    ) -> ProjectDivisionWithStats:
        """
        Get a project division with statistics.

        Args:
            division_id: Project division ID
            business_id: Business ID

        Returns:
            Project division with stats
        """
        # Get division
        division = await self.get_division(division_id, business_id)

        # Get transaction count and amounts
        transaction_stats = await self._get_transaction_stats(division_id, business_id)

        # Get document count
        document_count = await self._get_document_count(division_id, business_id)

        return ProjectDivisionWithStats(
            **division.model_dump(),
            transaction_count=transaction_stats["count"],
            document_count=document_count,
            total_amount=transaction_stats["net_amount"]
        )

    async def _validate_business_access(self, business_id: str) -> None:
        """Validate that the business exists."""
        response = self.supabase.table("businesses")\
            .select("id")\
            .eq("id", business_id)\
            .single()\
            .execute()

        if not response.data:
            raise ValueError("Business not found")

    async def _validate_unique_division_name(
        self,
        business_id: str,
        name: str,
        exclude_id: Optional[str] = None
    ) -> None:
        """Validate that division name is unique within business."""
        query = self.supabase.table("project_divisions")\
            .select("id")\
            .eq("business_id", business_id)\
            .ilike("name", name)\
            .eq("is_active", True)

        if exclude_id:
            query = query.neq("id", exclude_id)

        response = query.execute()

        if response.data:
            raise ValueError(f"Division name '{name}' already exists in this business")

    async def _validate_no_dependencies(self, division_id: str, business_id: str) -> None:
        """Validate that division has no dependent transactions or documents."""
        # Check transactions
        transaction_response = self.supabase.table("transactions")\
            .select("id")\
            .eq("project_division_id", division_id)\
            .eq("business_id", business_id)\
            .limit(1)\
            .execute()

        if transaction_response.data:
            raise ValueError("Cannot delete division with existing transactions")

        # Check documents
        document_response = self.supabase.table("documents")\
            .select("id")\
            .eq("project_division_id", division_id)\
            .eq("business_id", business_id)\
            .limit(1)\
            .execute()

        if document_response.data:
            raise ValueError("Cannot delete division with existing documents")

    async def _get_transaction_stats(self, division_id: str, business_id: str) -> Dict[str, Any]:
        """Get transaction statistics for a division."""
        # This would be implemented with actual queries
        # For now, return placeholder data
        return {
            "count": 0,
            "net_amount": 0.0
        }

    async def _get_document_count(self, division_id: str, business_id: str) -> int:
        """Get document count for a division."""
        # This would be implemented with actual queries
        # For now, return placeholder data
        return 0