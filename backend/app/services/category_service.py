"""
Category management service.
Handles business logic for category operations, hierarchical management, and categorization analytics.
"""
from typing import List, Dict, Any, Optional
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeNode
from app.db.supabase import get_supabase_client
from supabase import Client


class CategoryService:
    """Service class for category management operations."""

    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize category service.

        Args:
            supabase_client: Optional Supabase client, creates new one if not provided
        """
        self.supabase = supabase_client or get_supabase_client()

    async def create_category(self, category_data: CategoryCreate) -> CategoryResponse:
        """
        Create a new category with validation.

        Args:
            category_data: Category creation data

        Returns:
            Created category response

        Raises:
            ValueError: If validation fails
        """
        # Validate business exists and user has access
        await self._validate_business_access(category_data.business_id)

        # Validate parent category if specified
        if category_data.parent_id:
            await self._validate_parent_category(
                category_data.parent_id,
                category_data.business_id
            )

        # Check for duplicate category names within business (and parent)
        await self._validate_unique_category_name(
            category_data.business_id,
            category_data.category_name,
            category_data.parent_id
        )

        # Convert to dict
        category_dict = category_data.model_dump()

        response = self.supabase.table("categories").insert(category_dict).execute()

        if not response.data:
            raise ValueError("Failed to create category")

        return CategoryResponse(**response.data[0])

    async def update_category(self, category_id: str, category_data: CategoryUpdate) -> CategoryResponse:
        """
        Update an existing category.

        Args:
            category_id: Category ID to update
            category_data: Category update data

        Returns:
            Updated category response

        Raises:
            ValueError: If category not found or validation fails
        """
        # Get current category to validate business access and system status
        current_category = await self.get_category(category_id)

        # Check if it's a system category
        if current_category.is_system and category_data.category_name:
            raise ValueError("Cannot modify name of system categories")

        # Validate parent category if being changed
        if category_data.parent_id is not None:
            if category_data.parent_id == category_id:
                raise ValueError("Category cannot be its own parent")

            await self._validate_parent_category(
                category_data.parent_id,
                current_category.business_id
            )

        # Validate unique name if name is being changed
        if category_data.category_name:
            await self._validate_unique_category_name(
                current_category.business_id,
                category_data.category_name,
                current_category.parent_id,
                exclude_category_id=category_id
            )

        # Convert to dict
        update_dict = category_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise ValueError("No fields to update")

        response = self.supabase.table("categories")\
            .update(update_dict)\
            .eq("id", category_id)\
            .execute()

        if not response.data:
            raise ValueError("Category not found")

        return CategoryResponse(**response.data[0])

    async def get_category(self, category_id: str) -> CategoryResponse:
        """
        Get category by ID.

        Args:
            category_id: Category ID

        Returns:
            Category response

        Raises:
            ValueError: If category not found
        """
        response = self.supabase.table("categories")\
            .select("*")\
            .eq("id", category_id)\
            .single()\
            .execute()

        if not response.data:
            raise ValueError("Category not found")

        return CategoryResponse(**response.data)

    async def list_categories(
        self,
        business_id: str,
        category_type: Optional[str] = None,
        include_inactive: bool = False,
        include_system: bool = True
    ) -> List[CategoryResponse]:
        """
        List categories for a business.

        Args:
            business_id: Business ID
            category_type: Filter by category type (income/expense)
            include_inactive: Whether to include inactive categories
            include_system: Whether to include system categories

        Returns:
            List of category responses
        """
        query = self.supabase.table("categories").select("*").eq("business_id", business_id)

        if not include_inactive:
            query = query.eq("is_active", True)

        if not include_system:
            query = query.eq("is_system", False)

        if category_type:
            query = query.eq("category_type", category_type)

        # Order by display_order, then by name
        query = query.order("display_order").order("category_name")

        response = query.execute()

        return [CategoryResponse(**category) for category in response.data]

    async def get_category_hierarchy(self, business_id: str, include_inactive: bool = False) -> Dict[str, Any]:
        """
        Get hierarchical structure of categories for a business.

        Args:
            business_id: Business ID
            include_inactive: Whether to include inactive categories

        Returns:
            Hierarchical category structure
        """
        # Get all categories
        query = self.supabase.table("categories")\
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

        return {
            "root_categories": root_categories,
            "total_categories": len(categories)
        }

    async def delete_category(self, category_id: str) -> None:
        """
        Delete a category.

        Args:
            category_id: Category ID to delete

        Raises:
            ValueError: If category is system category or has dependencies
        """
        # Get category details
        category = await self.get_category(category_id)

        # Check if it's a system category
        if category.is_system:
            raise ValueError("System categories cannot be deleted")

        # Check if category has children
        children_response = self.supabase.table("categories")\
            .select("id")\
            .eq("parent_id", category_id)\
            .execute()

        if children_response.data:
            raise ValueError("Cannot delete category with subcategories")

        # Check if category has transactions (when transactions table exists)
        # For now, just delete the category

        response = self.supabase.table("categories")\
            .delete()\
            .eq("id", category_id)\
            .execute()

        if not response.data:
            raise ValueError("Category not found")

    async def get_category_summary(self, category_id: str) -> Dict[str, Any]:
        """
        Get detailed category summary with transaction statistics.

        Args:
            category_id: Category ID

        Returns:
            Category summary with statistics
        """
        # Get category details
        category = await self.get_category(category_id)

        # Get summary from view (when transactions exist)
        response = self.supabase.table("category_summaries")\
            .select("*")\
            .eq("id", category_id)\
            .single()\
            .execute()

        summary = response.data[0] if response.data else {
            "transaction_count": 0,
            "total_income": 0.00,
            "total_expenses": 0.00,
            "net_amount": 0.00
        }

        return {
            "category": category,
            "summary": summary
        }

    async def get_business_categories_summary(self, business_id: str) -> Dict[str, Any]:
        """
        Get summary of all categories for a business.

        Args:
            business_id: Business ID

        Returns:
            Business categories summary
        """
        categories = await self.list_categories(
            business_id,
            include_inactive=False,
            include_system=True
        )

        response = self.supabase.table("category_summaries")\
            .select("*")\
            .eq("business_id", business_id)\
            .eq("is_active", True)\
            .execute()

        category_summaries = response.data

        # Separate by type
        income_categories = [c for c in categories if c.category_type.value == "income"]
        expense_categories = [c for c in categories if c.category_type.value == "expense"]

        # Calculate totals
        total_income = sum(float(s.get("total_income", 0)) for s in category_summaries if s.get("category_type") == "income")
        total_expenses = sum(float(s.get("total_expenses", 0)) for s in category_summaries if s.get("category_type") == "expense")
        net_profit = total_income - total_expenses

        return {
            "business_id": business_id,
            "total_categories": len(categories),
            "income_categories": len(income_categories),
            "expense_categories": len(expense_categories),
            "system_categories": len([c for c in categories if c.is_system]),
            "custom_categories": len([c for c in categories if not c.is_system]),
            "categories": category_summaries,
            "totals": {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_profit": net_profit
            }
        }

    async def reorder_categories(self, business_id: str, category_orders: Dict[str, int]) -> None:
        """
        Update display order for multiple categories.

        Args:
            business_id: Business ID
            category_orders: Dict mapping category_id to new display_order

        Raises:
            ValueError: If validation fails
        """
        # Validate all categories belong to business
        category_ids = list(category_orders.keys())
        response = self.supabase.table("categories")\
            .select("id")\
            .eq("business_id", business_id)\
            .in_("id", category_ids)\
            .execute()

        if len(response.data) != len(category_ids):
            raise ValueError("Some categories not found or don't belong to this business")

        # Update display orders
        for category_id, display_order in category_orders.items():
            self.supabase.table("categories")\
                .update({"display_order": display_order})\
                .eq("id", category_id)\
                .execute()

    async def _validate_business_access(self, business_id: str) -> None:
        """
        Validate that the business exists.

        Args:
            business_id: Business ID to validate

        Raises:
            ValueError: If business doesn't exist
        """
        response = self.supabase.table("businesses")\
            .select("id")\
            .eq("id", business_id)\
            .single()\
            .execute()

        if not response.data:
            raise ValueError("Business not found")

    async def _validate_parent_category(self, parent_id: str, business_id: str) -> None:
        """
        Validate that parent category exists and belongs to the same business.

        Args:
            parent_id: Parent category ID
            business_id: Business ID

        Raises:
            ValueError: If parent category is invalid
        """
        response = self.supabase.table("categories")\
            .select("id, is_active")\
            .eq("id", parent_id)\
            .eq("business_id", business_id)\
            .single()\
            .execute()

        if not response.data:
            raise ValueError("Parent category not found")

        if not response.data["is_active"]:
            raise ValueError("Parent category is inactive")

    async def _validate_unique_category_name(
        self,
        business_id: str,
        category_name: str,
        parent_id: Optional[str] = None,
        exclude_category_id: Optional[str] = None
    ) -> None:
        """
        Validate that category name is unique within business and parent.

        Args:
            business_id: Business ID
            category_name: Category name to validate
            parent_id: Parent category ID (None for root categories)
            exclude_category_id: Category ID to exclude from check (for updates)

        Raises:
            ValueError: If name is not unique
        """
        query = self.supabase.table("categories")\
            .select("id")\
            .eq("business_id", business_id)\
            .eq("category_name", category_name)

        # Handle NULL parent_id comparison
        if parent_id is None:
            query = query.is_("parent_id", None)
        else:
            query = query.eq("parent_id", parent_id)

        if exclude_category_id:
            query = query.neq("id", exclude_category_id)

        response = query.execute()

        if response.data:
            context = "root level" if parent_id is None else "this subcategory"
            raise ValueError(f"Category name '{category_name}' already exists at {context}")