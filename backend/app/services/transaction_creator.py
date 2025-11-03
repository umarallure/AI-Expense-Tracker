"""
Transaction Creator Service
Automatically creates transactions from AI-extracted document data.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from loguru import logger
from supabase import Client


class TransactionCreator:
    """
    Service to create transactions from AI-extracted document data.
    
    Features:
    - Auto-creates transactions for high-confidence extractions (>0.85)
    - Links transactions to source documents
    - Matches categories dynamically
    - Handles missing optional fields
    - Sets appropriate status based on confidence
    """
    
    def __init__(self, confidence_threshold: float = 0.85):
        """
        Initialize TransactionCreator.
        
        Args:
            confidence_threshold: Minimum confidence to auto-create (default 0.85)
        """
        self.confidence_threshold = confidence_threshold
        
        # Field weights for confidence calculation
        self.FIELD_WEIGHTS = {
            "amount": 0.30,
            "vendor": 0.20,
            "date": 0.20,
            "category_id": 0.15,
            "description": 0.10,
            "payment_method": 0.05
        }
    
    async def create_from_document(
        self,
        document_id: str,
        business_id: str,
        account_id: str,
        user_id: str,
        extracted_data: Dict[str, Any],
        confidence_score: float,
        supabase_client: Client
    ) -> Optional[Dict[str, Any]]:
        """
        Create transaction(s) from extracted document data.
        
        Args:
            document_id: Source document ID
            business_id: Business ID
            account_id: Account ID for the transaction
            user_id: User who uploaded the document
            extracted_data: AI-extracted data (single or multi-transaction)
            confidence_score: Overall confidence score
            supabase_client: Supabase client
            
        Returns:
            Created transaction data or None if not created
        """
        try:
            # Check if this is multi-transaction data
            if self._is_multi_transaction_data(extracted_data):
                return await self._create_multiple_transactions(
                    document_id, business_id, account_id, user_id, 
                    extracted_data, confidence_score, supabase_client
                )
            
            # Single transaction creation (existing logic)
            return await self._create_single_transaction(
                document_id, business_id, account_id, user_id,
                extracted_data, confidence_score, supabase_client
            )
            
        except Exception as e:
            logger.error(f"Failed to create transaction(s) from document {document_id}: {str(e)}")
            return None
    
    async def _create_single_transaction(
        self,
        document_id: str,
        business_id: str,
        account_id: str,
        user_id: str,
        extracted_data: Dict[str, Any],
        confidence_score: float,
        supabase_client: Client
    ) -> Optional[Dict[str, Any]]:
        """
        Create a single transaction from extracted data.
        
        Args:
            document_id: Source document ID
            business_id: Business ID
            account_id: Account ID
            user_id: User ID
            extracted_data: Extracted data
            confidence_score: Confidence score
            supabase_client: Supabase client
            
        Returns:
            Created transaction data or None
        """
        try:
            # Get required fields
            vendor = extracted_data.get("vendor")
            amount = extracted_data.get("amount")
            date = extracted_data.get("date")
            
            if not vendor or amount is None:
                logger.warning(f"Missing required fields for document {document_id}: vendor={vendor}, amount={amount}")
                return None
            
            # Get category_id
            category_name = extracted_data.get("category")
            category_id = None
            if category_name:
                category_id = await self._match_category(business_id, category_name, supabase_client)
            
            # Store category_id in extracted_data for status determination
            if category_id:
                extracted_data["category_id"] = category_id
            
            # Parse date
            if isinstance(date, str):
                try:
                    parsed_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                except Exception as e:
                    logger.warning(f"Failed to parse date '{date}': {e}")
                    parsed_date = datetime.utcnow()
            else:
                parsed_date = date if date else datetime.utcnow()
            
            # Build transaction data
            transaction_data = {
                "business_id": business_id,
                "account_id": account_id,
                "user_id": user_id,
                "vendor": vendor,
                "amount": float(amount),
                "currency": "USD",
                "description": extracted_data.get("description") or f"Auto-created from {vendor}",
                "date": parsed_date.isoformat(),
                "is_income": extracted_data.get("is_income", False),
                "status": self._determine_status(confidence_score, extracted_data),
                "notes": self._generate_notes(extracted_data, confidence_score),
                "taxes_fees": extracted_data.get("taxes_fees"),
                "payment_method": extracted_data.get("payment_method"),
                "recipient_id": extracted_data.get("recipient_id"),
                "source_document_id": document_id
            }
            
            # Add category if available
            if category_id:
                transaction_data["category_id"] = category_id
            
            # Create transaction
            response = supabase_client.table("transactions").insert(transaction_data).execute()
            
            if not response.data:
                logger.error(f"Failed to create transaction - no data returned")
                return None
            
            created_transaction = response.data[0]
            
            logger.info(
                f"Created transaction {created_transaction['id']} from document {document_id}: "
                f"{vendor} - ${amount}"
            )
            
            return created_transaction
            
        except Exception as e:
            logger.error(f"Failed to create single transaction from document {document_id}: {str(e)}")
            return None
    
    async def _match_category(
        self,
        business_id: str,
        category_name: Optional[str],
        supabase_client: Client
    ) -> Optional[str]:
        """
        Match extracted category name to actual category ID.
        
        Args:
            business_id: Business ID
            category_name: Category name from extraction
            supabase_client: Supabase client
            
        Returns:
            Category ID or None if not matched
        """
        if not category_name:
            return None
        
        try:
            # Try exact match first
            response = supabase_client.table("categories").select("id, category_name").eq(
                "business_id", business_id
            ).ilike("category_name", category_name).execute()
            
            if response.data and len(response.data) > 0:
                category_id = response.data[0]["id"]
                logger.debug(f"Matched category '{category_name}' to ID {category_id}")
                return category_id
            
            # Try partial match (case-insensitive contains)
            response = supabase_client.table("categories").select("id, category_name").eq(
                "business_id", business_id
            ).execute()
            
            if response.data:
                # Manual fuzzy matching
                category_name_lower = category_name.lower()
                for cat in response.data:
                    cat_name_lower = cat["category_name"].lower()
                    if category_name_lower in cat_name_lower or cat_name_lower in category_name_lower:
                        category_id = cat["id"]
                        logger.debug(
                            f"Fuzzy matched category '{category_name}' to "
                            f"'{cat['category_name']}' (ID: {category_id})"
                        )
                        return category_id
            
            logger.debug(f"No category match found for '{category_name}'")
            return None
            
        except Exception as e:
            logger.warning(f"Category matching failed: {str(e)}")
            return None
    
    def _check_missing_required_fields(self, extracted_data: Dict[str, Any]) -> List[str]:
        """
        Check for missing required fields that would prevent auto-approval.
        
        Args:
            extracted_data: AI-extracted data
            
        Returns:
            List of missing field names
        """
        missing_fields = []
        
        # Check category_id
        if not extracted_data.get("category_id"):
            missing_fields.append("category")
        
        # Check account_id (this would need to be provided by the calling code)
        # For now, we'll assume it's provided, but this could be enhanced later
        
        # Check payment_method
        if not extracted_data.get("payment_method"):
            missing_fields.append("payment_method")
        
        # Check vendor (unless it's a transfer/deposit)
        description = extracted_data.get("description") or ""
        is_transfer_or_deposit = (
            "transfer" in description.lower() or 
            "deposit" in description.lower()
        )
        
        if not extracted_data.get("vendor") and not is_transfer_or_deposit:
            missing_fields.append("vendor")
        
        # Check amount
        amount = extracted_data.get("amount")
        if not amount or float(amount) <= 0:
            missing_fields.append("amount")
        
        return missing_fields
    
    def _determine_status(self, confidence_score: float, extracted_data: Dict[str, Any]) -> str:
        """
        Determine transaction status based on confidence score and missing fields.
        
        Args:
            confidence_score: Overall confidence score
            extracted_data: AI-extracted data
            
        Returns:
            Transaction status string
        """
        # First check for missing required fields - if any are missing, 
        # transaction cannot be auto-approved regardless of confidence
        missing_fields = self._check_missing_required_fields(extracted_data)
        if missing_fields:
            logger.info(
                f"Transaction has missing required fields {missing_fields}. "
                f"Setting status to 'pending' for manual review."
            )
            return "pending"  # Requires manual review to complete missing fields
        
        # If all required fields are present, use confidence-based logic
        if confidence_score >= 0.95:
            return "approved"  # Very high confidence - auto-approve
        elif confidence_score >= 0.85:
            return "pending"  # High confidence - pending approval
        else:
            return "draft"  # Lower confidence - needs review
    
    def _generate_notes(
        self,
        extracted_data: Dict[str, Any],
        confidence_score: float,
        transaction_index: int = None
    ) -> str:
        """
        Generate notes for the transaction.
        
        Args:
            extracted_data: Extracted data
            confidence_score: Overall confidence score
            transaction_index: Index for multi-transaction (optional)
            
        Returns:
            Notes string
        """
        notes_parts = [
            "Auto-created from document extraction",
            f"Confidence: {confidence_score:.1%}",
            "Category selected by AI"
        ]
        
        # Add transaction index if part of multi-transaction
        if transaction_index is not None:
            notes_parts.insert(1, f"Transaction #{transaction_index + 1} from multi-transaction document")
        
        # Check for missing required fields
        missing_fields = self._check_missing_required_fields(extracted_data)
        if missing_fields:
            notes_parts.append(
                f"⚠️ MISSING REQUIRED FIELDS: {', '.join(missing_fields).upper()}. "
                "Transaction set to 'pending' for manual review."
            )
        
        # Add field confidence info
        field_confidence = extracted_data.get("field_confidence", {})
        if field_confidence:
            low_confidence_fields = [
                field for field, conf in field_confidence.items()
                if conf < 0.70
            ]
            if low_confidence_fields:
                notes_parts.append(
                    f"Low confidence fields: {', '.join(low_confidence_fields)}"
                )
        
        # Add line items if present
        line_items = extracted_data.get("line_items", [])
        if line_items and len(line_items) > 0:
            notes_parts.append(f"Contains {len(line_items)} line items")
        
        return "\n".join(notes_parts)
    
    async def should_create_transaction(
        self,
        confidence_score: float,
        extracted_data: Dict[str, Any]
    ) -> bool:
        """
        Determine if transaction should be auto-created.
        
        Args:
            confidence_score: Overall confidence score
            extracted_data: Extracted data
            
        Returns:
            True if should create, False otherwise
        """
        # Check confidence threshold
        if confidence_score < self.confidence_threshold:
            return False
        
        # Check required fields
        if not extracted_data.get("vendor"):
            return False
        if not extracted_data.get("amount"):
            return False
        if not extracted_data.get("date"):
            return False
        
            return True
    
    def _is_multi_transaction_data(self, extracted_data: Dict[str, Any]) -> bool:
        """
        Check if extracted data contains multiple transactions
        
        Args:
            extracted_data: AI-extracted data
            
        Returns:
            True if multi-transaction data
        """
        if extracted_data.get("extraction_type") == "multi_transaction":
            return True
        
        transactions = extracted_data.get("transactions", [])
        return isinstance(transactions, list) and len(transactions) > 1
    
    async def _create_multiple_transactions(
        self,
        document_id: str,
        business_id: str,
        account_id: str,
        user_id: str,
        extracted_data: Dict[str, Any],
        overall_confidence: float,
        supabase_client: Client
    ) -> Optional[Dict[str, Any]]:
        """
        Create multiple transactions from multi-transaction extraction
        
        Args:
            document_id: Source document ID
            business_id: Business ID
            account_id: Account ID
            user_id: User ID
            extracted_data: Multi-transaction extraction data
            overall_confidence: Overall confidence score
            supabase_client: Supabase client
            
        Returns:
            Summary of created transactions
        """
        try:
            transactions = extracted_data.get("transactions", [])
            if not transactions:
                logger.warning(f"No transactions found in multi-transaction data for document {document_id}")
                return None
            
            # Check overall confidence threshold
            if overall_confidence < self.confidence_threshold:
                logger.info(
                    f"Document {document_id} overall confidence {overall_confidence:.2f} "
                    f"below threshold {self.confidence_threshold}. Skipping multi-transaction creation."
                )
                return None
            
            created_transactions = []
            failed_transactions = []
            
            # Process each transaction
            for i, tx_data in enumerate(transactions):
                try:
                    # Calculate individual transaction confidence
                    tx_confidence = self._calculate_transaction_confidence(tx_data)
                    
                    # Skip transactions below threshold
                    if tx_confidence < self.confidence_threshold:
                        logger.debug(f"Transaction {i} confidence {tx_confidence:.2f} below threshold, skipping")
                        failed_transactions.append({"index": i, "reason": "low_confidence", "confidence": tx_confidence})
                        continue
                    
                    # Create individual transaction
                    created_tx = await self._create_single_transaction_from_data(
                        document_id, business_id, account_id, user_id, tx_data, 
                        tx_confidence, supabase_client, transaction_index=i
                    )
                    
                    if created_tx:
                        created_transactions.append(created_tx)
                    else:
                        failed_transactions.append({"index": i, "reason": "creation_failed"})
                        
                except Exception as e:
                    logger.error(f"Failed to create transaction {i} from document {document_id}: {str(e)}")
                    failed_transactions.append({"index": i, "reason": "exception", "error": str(e)})
            
            # Update document with transaction links
            if created_transactions:
                transaction_ids = [tx["id"] for tx in created_transactions]
                await self._link_document_to_transactions(document_id, transaction_ids, supabase_client)
            
            # Log summary
            logger.info(
                f"✅ Multi-transaction creation completed for document {document_id}. "
                f"Created: {len(created_transactions)}, Failed: {len(failed_transactions)}, "
                f"Overall confidence: {overall_confidence:.2f}"
            )
            
            return {
                "document_id": document_id,
                "extraction_type": "multi_transaction",
                "total_transactions": len(transactions),
                "created_transactions": len(created_transactions),
                "failed_transactions": len(failed_transactions),
                "transaction_ids": [tx["id"] for tx in created_transactions],
                "overall_confidence": overall_confidence,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create multiple transactions from document {document_id}: {str(e)}")
            return None
    
    async def _create_single_transaction_from_data(
        self,
        document_id: str,
        business_id: str,
        account_id: str,
        user_id: str,
        tx_data: Dict[str, Any],
        confidence_score: float,
        supabase_client: Client,
        transaction_index: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Create a single transaction from transaction data
        
        Args:
            document_id: Source document ID
            business_id: Business ID
            account_id: Account ID
            user_id: User ID
            tx_data: Individual transaction data
            confidence_score: Transaction confidence score
            supabase_client: Supabase client
            transaction_index: Index in multi-transaction batch
            
        Returns:
            Created transaction data or None
        """
        try:
            # Validate required fields
            vendor = tx_data.get("vendor")
            amount = tx_data.get("amount")
            date = tx_data.get("date")
            
            if not vendor or amount is None or not date:
                logger.debug(f"Transaction {transaction_index} missing required fields: vendor={vendor}, amount={amount}, date={date}")
                return None
            
            # Get category_id
            category_id = tx_data.get("category_id")
            
            # Parse date
            if isinstance(date, str):
                try:
                    parsed_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                except Exception as e:
                    logger.warning(f"Failed to parse date '{date}' for transaction {transaction_index}: {e}")
                    parsed_date = datetime.utcnow()
            else:
                parsed_date = date
            
            # Build transaction data
            transaction_data = {
                "business_id": business_id,
                "account_id": account_id,
                "user_id": user_id,
                "vendor": vendor,
                "amount": float(amount),
                "currency": "USD",
                "description": tx_data.get("description") or f"Auto-created from {vendor}",
                "date": parsed_date.isoformat(),
                "is_income": tx_data.get("is_income", False),
                "status": self._determine_status(confidence_score, tx_data),
                "notes": self._generate_notes(tx_data, confidence_score, transaction_index),
                "taxes_fees": tx_data.get("taxes_fees"),
                "payment_method": tx_data.get("payment_method"),
                "recipient_id": tx_data.get("recipient_id"),
                "source_document_id": document_id,
                "_transaction_index": transaction_index  # Track position in multi-transaction
            }
            
            # Add category if available
            if category_id:
                transaction_data["category_id"] = category_id
            
            # Create transaction
            response = supabase_client.table("transactions").insert(transaction_data).execute()
            
            if not response.data:
                logger.error(f"Failed to create transaction {transaction_index} - no data returned")
                return None
            
            created_transaction = response.data[0]
            
            logger.debug(
                f"Created transaction {created_transaction['id']} from document {document_id} "
                f"(index {transaction_index}): {vendor} - ${amount}"
            )
            
            return created_transaction
            
        except Exception as e:
            logger.error(f"Failed to create transaction {transaction_index} from document {document_id}: {str(e)}")
            return None
    
    async def _link_document_to_transactions(
        self,
        document_id: str,
        transaction_ids: List[str],
        supabase_client: Client
    ) -> None:
        """
        Link document to multiple transactions
        
        Args:
            document_id: Document ID
            transaction_ids: List of transaction IDs
            supabase_client: Supabase client
        """
        try:
            # For now, link to the first transaction as primary
            # TODO: Consider adding a separate relationship table for multi-transaction documents
            primary_transaction_id = transaction_ids[0]
            
            supabase_client.table("documents").update({
                "transaction_id": primary_transaction_id,
                "auto_created_transaction": True,
                "multi_transaction_count": len(transaction_ids),
                "linked_transaction_ids": transaction_ids
            }).eq("id", document_id).execute()
            
            logger.debug(f"Linked document {document_id} to {len(transaction_ids)} transactions")
            
        except Exception as e:
            logger.error(f"Failed to link document {document_id} to transactions: {str(e)}")
    
    def _calculate_transaction_confidence(self, tx_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for individual transaction
        
        Args:
            tx_data: Transaction data
            
        Returns:
            Confidence score
        """
        try:
            field_confidence = tx_data.get("field_confidence", {})
            
            if not field_confidence:
                # Estimate confidence based on available fields
                confidence = 0.0
                if tx_data.get("vendor"):
                    confidence += 0.3
                if tx_data.get("amount") is not None:
                    confidence += 0.4
                if tx_data.get("date"):
                    confidence += 0.3
                return min(confidence, 1.0)
            
            # Calculate weighted confidence
            total_weight = 0.0
            weighted_sum = 0.0
            
            for field, confidence in field_confidence.items():
                weight = self.FIELD_WEIGHTS.get(field, 0.05)
                weighted_sum += confidence * weight
                total_weight += weight
            
            return weighted_sum / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate transaction confidence: {str(e)}")
            return 0.0
