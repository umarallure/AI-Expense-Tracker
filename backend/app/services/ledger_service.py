"""
Ledger service for managing account balance changes and transaction history.
Handles ledger entries when transactions are approved.
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from app.db.supabase import get_supabase_admin_client
from supabase import Client


class LedgerService:
    """Service for managing ledger entries and account balance updates."""

    @staticmethod
    async def create_ledger_entry(
        supabase: Client,
        business_id: str,
        account_id: str,
        transaction_id: str,
        change_amount: Decimal,
        transaction_type: str,
        user_id: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a ledger entry for a transaction approval.

        Args:
            supabase: Supabase client (will be replaced with admin client)
            business_id: Business ID
            account_id: Account ID
            transaction_id: Transaction ID
            change_amount: Amount to change (positive for income, negative for expense)
            transaction_type: 'income' or 'expense'
            user_id: User who approved the transaction
            description: Optional description

        Returns:
            Created ledger entry
        """
        # Use admin client to bypass RLS
        admin_client = get_supabase_admin_client()
        
        try:
            # Get current account balance
            account_response = admin_client.table("accounts")\
                .select("current_balance")\
                .eq("id", account_id)\
                .single()\
                .execute()

            if not account_response.data:
                raise ValueError(f"Account {account_id} not found")

            amount_before = Decimal(str(account_response.data["current_balance"]))

            # Calculate new balance
            amount_after = amount_before + change_amount

            # Create ledger entry
            ledger_data = {
                "business_id": str(business_id),
                "account_id": str(account_id),
                "transaction_id": str(transaction_id),
                "amount_before": float(amount_before),
                "amount_after": float(amount_after),
                "change_amount": float(change_amount),
                "transaction_type": transaction_type,
                "description": description,
                "created_by": str(user_id)
            }

            ledger_response = admin_client.table("ledger").insert(ledger_data).execute()

            if not ledger_response.data:
                raise ValueError("Failed to create ledger entry")

            # Update account balance
            update_data = {
                "current_balance": float(amount_after),
                "available_balance": float(amount_after),  # Also update available balance for approved transactions
                "updated_at": datetime.utcnow().isoformat()
            }

            # Update account balance
            account_response = admin_client.table("accounts")\
                .update(update_data)\
                .eq("id", account_id)\
                .execute()

            if not account_response.data:
                raise ValueError("Failed to update account balance")

            return ledger_response.data[0]

        except Exception as e:
            raise ValueError(f"Failed to create ledger entry: {str(e)}")

    @staticmethod
    async def get_ledger_entries(
        supabase: Client,
        business_id: str,
        account_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get ledger entries for a business or specific account.

        Args:
            supabase: Supabase client (will use admin client for consistency)
            business_id: Business ID
            account_id: Optional account ID filter
            limit: Maximum number of entries to return
            offset: Offset for pagination

        Returns:
            List of ledger entries
        """
        # Use admin client for consistency
        admin_client = get_supabase_admin_client()
        
        try:
            query = admin_client.table("ledger")\
                .select("*")\
                .eq("business_id", business_id)\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)

            if account_id:
                query = query.eq("account_id", account_id)

            response = query.execute()

            return response.data or []

        except Exception as e:
            raise ValueError(f"Failed to get ledger entries: {str(e)}")

    @staticmethod
    async def get_account_balance_history(
        supabase: Client,
        account_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get balance history for a specific account.

        Args:
            supabase: Supabase client (will use admin client for consistency)
            account_id: Account ID
            limit: Maximum number of entries to return

        Returns:
            List of balance changes with timestamps
        """
        # Use admin client for consistency
        admin_client = get_supabase_admin_client()
        
        try:
            response = admin_client.table("ledger")\
                .select("amount_before, amount_after, change_amount, transaction_type, description, created_at")\
                .eq("account_id", account_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()

            return response.data or []

        except Exception as e:
            raise ValueError(f"Failed to get account balance history: {str(e)}")

    @staticmethod
    async def get_transaction_ledger_entry(
        supabase: Client,
        transaction_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get ledger entry for a specific transaction.

        Args:
            supabase: Supabase client (will use admin client for consistency)
            transaction_id: Transaction ID

        Returns:
            Ledger entry if exists, None otherwise
        """
        # Use admin client for consistency
        admin_client = get_supabase_admin_client()
        
        try:
            response = admin_client.table("ledger")\
                .select("*")\
                .eq("transaction_id", transaction_id)\
                .single()\
                .execute()

            return response.data

        except Exception:
            # Return None if not found
            return None

    @staticmethod
    async def calculate_account_balance_from_ledger(
        supabase: Client,
        account_id: str,
        start_date: Optional[datetime] = None
    ) -> Decimal:
        """
        Calculate account balance from ledger entries.
        Useful for reconciliation or auditing.

        Args:
            supabase: Supabase client (will use admin client for consistency)
            account_id: Account ID
            start_date: Optional start date for calculation

        Returns:
            Calculated balance from ledger
        """
        # Use admin client for consistency
        admin_client = get_supabase_admin_client()
        
        try:
            query = admin_client.table("ledger")\
                .select("change_amount")\
                .eq("account_id", account_id)\
                .order("created_at", desc=True)

            if start_date:
                query = query.gte("created_at", start_date.isoformat())

            response = query.execute()

            total_change = Decimal('0.00')
            for entry in response.data or []:
                total_change += Decimal(str(entry["change_amount"]))

            return total_change

        except Exception as e:
            raise ValueError(f"Failed to calculate account balance from ledger: {str(e)}")


# Global instance for easy importing
ledger_service = LedgerService()