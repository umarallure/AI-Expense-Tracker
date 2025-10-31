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
        Create a transaction from extracted document data.
        
        Args:
            document_id: Source document ID
            business_id: Business ID
            account_id: Account ID for the transaction
            user_id: User who uploaded the document
            extracted_data: AI-extracted data
            confidence_score: Overall confidence score
            supabase_client: Supabase client
            
        Returns:
            Created transaction data or None if not created
            
        Raises:
            Exception: If transaction creation fails
        """
        try:
            # Check if confidence meets threshold
            if confidence_score < self.confidence_threshold:
                logger.info(
                    f"Document {document_id} confidence {confidence_score:.2f} "
                    f"below threshold {self.confidence_threshold}. Skipping auto-creation."
                )
                return None
            
            # Validate required fields
            vendor = extracted_data.get("vendor")
            amount = extracted_data.get("amount")
            date = extracted_data.get("date")
            
            if not vendor or not amount or not date:
                logger.warning(
                    f"Document {document_id} missing required fields. "
                    f"Vendor: {vendor}, Amount: {amount}, Date: {date}"
                )
                return None
            
            # Get category_id from AI extraction (no longer needs matching)
            category_id = extracted_data.get("category_id")
            
            # Parse date string to datetime if needed
            if isinstance(date, str):
                try:
                    date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                except Exception as e:
                    logger.warning(f"Failed to parse date '{date}': {e}")
                    date = datetime.utcnow()
            
            # Build transaction data
            transaction_data = {
                "business_id": business_id,
                "account_id": account_id,
                "user_id": user_id,
                "vendor": vendor,
                "amount": float(amount),
                "currency": "USD",  # TODO: Extract currency from document
                "description": extracted_data.get("description") or f"Auto-created from {vendor}",
                "date": date.isoformat(),
                "is_income": extracted_data.get("is_income", False),
                "status": self._determine_status(confidence_score, extracted_data),
                "notes": self._generate_notes(extracted_data, confidence_score),
                "taxes_fees": extracted_data.get("taxes_fees"),
                "payment_method": extracted_data.get("payment_method"),
                "recipient_id": extracted_data.get("recipient_id"),
                "source_document_id": document_id  # Link to source document
            }
            
            # Add category if matched
            if category_id:
                transaction_data["category_id"] = category_id
            
            # Create transaction in database
            response = supabase_client.table("transactions").insert(
                transaction_data
            ).execute()
            
            if not response.data:
                raise Exception("Failed to create transaction - no data returned")
            
            created_transaction = response.data[0]
            transaction_id = created_transaction.get("id")
            
            # Update document with transaction link
            supabase_client.table("documents").update({
                "transaction_id": transaction_id,
                "auto_created_transaction": True
            }).eq("id", document_id).execute()
            
            logger.info(
                f"✅ Auto-created transaction {transaction_id} from document {document_id}. "
                f"Vendor: {vendor}, Amount: ${amount}, Confidence: {confidence_score:.2f}"
            )
            
            return created_transaction
            
        except Exception as e:
            logger.error(f"Failed to create transaction from document {document_id}: {str(e)}")
            # Don't raise - we don't want to fail document processing
            # Just log and return None
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
        description = extracted_data.get("description", "").lower()
        is_transfer_or_deposit = (
            "transfer" in description or 
            "deposit" in description
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
        confidence_score: float
    ) -> str:
        """
        Generate notes for the transaction.
        
        Args:
            extracted_data: Extracted data
            confidence_score: Overall confidence score
            
        Returns:
            Notes string
        """
        notes_parts = [
            "Auto-created from document extraction",
            f"Confidence: {confidence_score:.1%}",
            "Category selected by AI"
        ]
        
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
