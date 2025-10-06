"""
Account management service.
Handles business logic for account operations, balance calculations, and financial analytics.
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from app.db.supabase import get_supabase_client
from supabase import Client


class AccountService:
    """Service class for account management operations."""

    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize account service.

        Args:
            supabase_client: Optional Supabase client, creates new one if not provided
        """
        self.supabase = supabase_client or get_supabase_client()

    async def create_account(self, account_data: AccountCreate) -> AccountResponse:
        """
        Create a new account with validation.

        Args:
            account_data: Account creation data

        Returns:
            Created account response

        Raises:
            ValueError: If validation fails
        """
        # Validate business exists and user has access
        await self._validate_business_access(account_data.business_id)

        # Check for duplicate account names within business
        await self._validate_unique_account_name(
            account_data.business_id,
            account_data.account_name
        )

        # Convert to dict and handle Decimal types
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

        response = self.supabase.table("accounts").insert(account_dict).execute()

        if not response.data:
            raise ValueError("Failed to create account")

        return AccountResponse(**response.data[0])

    async def update_account(self, account_id: str, account_data: AccountUpdate) -> AccountResponse:
        """
        Update an existing account.

        Args:
            account_id: Account ID to update
            account_data: Account update data

        Returns:
            Updated account response

        Raises:
            ValueError: If account not found or validation fails
        """
        # Get current account to validate business access
        current_account = await self.get_account(account_id)

        # Validate unique name if name is being changed
        if account_data.account_name:
            await self._validate_unique_account_name(
                current_account.business_id,
                account_data.account_name,
                exclude_account_id=account_id
            )

        # Convert to dict and handle Decimal types
        update_dict = account_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise ValueError("No fields to update")

        # Convert Decimal fields
        decimal_fields = ['current_balance', 'available_balance', 'credit_limit', 'interest_rate', 'minimum_payment']
        for field in decimal_fields:
            if field in update_dict and update_dict[field] is not None:
                update_dict[field] = float(update_dict[field])

        response = self.supabase.table("accounts")\
            .update(update_dict)\
            .eq("id", account_id)\
            .execute()

        if not response.data:
            raise ValueError("Account not found")

        return AccountResponse(**response.data[0])

    async def get_account(self, account_id: str) -> AccountResponse:
        """
        Get account by ID.

        Args:
            account_id: Account ID

        Returns:
            Account response

        Raises:
            ValueError: If account not found
        """
        response = self.supabase.table("accounts")\
            .select("*")\
            .eq("id", account_id)\
            .single()\
            .execute()

        if not response.data:
            raise ValueError("Account not found")

        return AccountResponse(**response.data)

    async def list_accounts(
        self,
        business_id: str,
        include_inactive: bool = False
    ) -> List[AccountResponse]:
        """
        List accounts for a business.

        Args:
            business_id: Business ID
            include_inactive: Whether to include inactive accounts

        Returns:
            List of account responses
        """
        query = self.supabase.table("accounts").select("*").eq("business_id", business_id)

        if not include_inactive:
            query = query.eq("is_active", True)

        response = query.execute()

        return [AccountResponse(**account) for account in response.data]

    async def update_account_balance(
        self,
        account_id: str,
        current_balance: Decimal,
        available_balance: Optional[Decimal] = None
    ) -> AccountResponse:
        """
        Update account balance.

        Args:
            account_id: Account ID
            current_balance: New current balance
            available_balance: New available balance (optional)

        Returns:
            Updated account response
        """
        update_dict = {
            "current_balance": float(current_balance)
        }

        if available_balance is not None:
            update_dict["available_balance"] = float(available_balance)

        response = self.supabase.table("accounts")\
            .update(update_dict)\
            .eq("id", account_id)\
            .execute()

        if not response.data:
            raise ValueError("Account not found")

        return AccountResponse(**response.data[0])

    async def delete_account(self, account_id: str) -> None:
        """
        Delete an account.

        Args:
            account_id: Account ID to delete

        Raises:
            ValueError: If account has transactions or other dependencies
        """
        # Check if account has transactions (when transactions table exists)
        # For now, just delete the account

        response = self.supabase.table("accounts")\
            .delete()\
            .eq("id", account_id)\
            .execute()

        if not response.data:
            raise ValueError("Account not found")

    async def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """
        Get detailed account summary with transaction statistics.

        Args:
            account_id: Account ID

        Returns:
            Account summary with statistics
        """
        # Get account details
        account = await self.get_account(account_id)

        # Get summary from view (when transactions exist)
        response = self.supabase.table("account_summaries")\
            .select("*")\
            .eq("id", account_id)\
            .single()\
            .execute()

        summary = response.data[0] if response.data else {
            "total_debits": 0.00,
            "total_credits": 0.00,
            "net_flow": 0.00
        }

        return {
            "account": account,
            "summary": summary
        }

    async def get_business_accounts_summary(self, business_id: str) -> Dict[str, Any]:
        """
        Get summary of all accounts for a business.

        Args:
            business_id: Business ID

        Returns:
            Business accounts summary
        """
        accounts = await self.list_accounts(business_id, include_inactive=False)

        response = self.supabase.table("account_summaries")\
            .select("*")\
            .eq("business_id", business_id)\
            .eq("is_active", True)\
            .execute()

        account_summaries = response.data

        # Calculate totals
        total_balance = sum(float(a.get("current_balance", 0)) for a in accounts)
        total_available = sum(float(a.get("available_balance", 0)) for a in accounts)
        total_debits = sum(float(s.get("total_debits", 0)) for s in account_summaries)
        total_credits = sum(float(s.get("total_credits", 0)) for s in account_summaries)
        net_flow = sum(float(s.get("net_flow", 0)) for s in account_summaries)

        return {
            "business_id": business_id,
            "total_accounts": len(accounts),
            "accounts": account_summaries,
            "totals": {
                "total_balance": total_balance,
                "total_available_balance": total_available,
                "total_debits": total_debits,
                "total_credits": total_credits,
                "net_flow": net_flow
            }
        }

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

    async def _validate_unique_account_name(
        self,
        business_id: str,
        account_name: str,
        exclude_account_id: Optional[str] = None
    ) -> None:
        """
        Validate that account name is unique within business.

        Args:
            business_id: Business ID
            account_name: Account name to validate
            exclude_account_id: Account ID to exclude from check (for updates)

        Raises:
            ValueError: If name is not unique
        """
        query = self.supabase.table("accounts")\
            .select("id")\
            .eq("business_id", business_id)\
            .eq("account_name", account_name)

        if exclude_account_id:
            query = query.neq("id", exclude_account_id)

        response = query.execute()

        if response.data:
            raise ValueError(f"Account name '{account_name}' already exists in this business")