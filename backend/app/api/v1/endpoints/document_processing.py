"""
Document Processing endpoints for AI extraction pipeline.
Handles document processing, text extraction, and status checking.
"""
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from loguru import logger
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from pathlib import Path
import tempfile
import os

from app.schemas.auth import MessageResponse
from app.core.security import get_current_user
from app.core.deps import check_business_permission, get_business_access
from app.db.supabase import get_supabase_client
from supabase import Client

from app.services.document_processor import DocumentProcessor
from app.services.document_classifier import DocumentClassifier
from app.services.document_chunker import DocumentChunker
from app.services.ai import DataExtractor, ConfidenceScorer
from app.services.transaction_creator import TransactionCreator
from app.core.config import get_settings

router = APIRouter(prefix="/document-processing", tags=["Document Processing"])

# Initialize document processor and AI services
settings = get_settings()
document_processor = DocumentProcessor()
document_classifier = DocumentClassifier()
document_chunker = DocumentChunker(
    max_chunk_size=4000,  # Reduced for better AI processing (was 8000)
    max_transactions_per_chunk=30  # Reduced to prevent token limit issues (was 50)
)
data_extractor = DataExtractor()
confidence_scorer = ConfidenceScorer()
transaction_creator = TransactionCreator(confidence_threshold=0.85)


async def verify_document_access(
    document_id: str,
    current_user: Dict[str, Any],
    supabase: Client,
    required_role: str = "member"
) -> Dict[str, Any]:
    """
    Verify user has access to document's business.
    
    Args:
        document_id: Document ID
        current_user: Current user info
        supabase: Supabase client
        required_role: Required role level (member, accountant, admin, owner)
        
    Returns:
        Document data
        
    Raises:
        HTTPException: If document not found or user lacks permission
    """
    # Get document
    response = supabase.table("documents").select("*").eq("id", document_id).execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    document = response.data[0]
    business_id = document.get("business_id")
    user_id = current_user.get("user_id")
    
    # Check business membership
    member_response = supabase.table("business_members").select("*").eq(
        "business_id", business_id
    ).eq("user_id", user_id).eq("status", "active").execute()
    
    if not member_response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this business"
        )
    
    # Check permission level
    member = member_response.data[0]
    role = member.get("role", "viewer")
    
    permission_levels = {
        "owner": 4,
        "admin": 3,
        "accountant": 2,
        "member": 2,
        "viewer": 1
    }
    
    user_level = permission_levels.get(role, 0)
    required_level = permission_levels.get(required_role, 0)
    
    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {required_role}"
        )
    
    return document


async def download_document_from_storage(
    document_id: str,
    storage_path: str,
    supabase: Client
) -> Path:
    """
    Download document from Supabase Storage to temporary file
    
    Args:
        document_id: Document ID
        storage_path: Path in Supabase Storage
        supabase: Supabase client
        
    Returns:
        Path to downloaded temporary file
    """
    try:
        # Download file from storage
        file_data = supabase.storage.from_("documents").download(storage_path)
        
        # Get file extension from storage path
        file_ext = Path(storage_path).suffix
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_ext,
            prefix=f"doc_{document_id}_"
        )
        
        # Write file data
        temp_file.write(file_data)
        temp_file.close()
        
        return Path(temp_file.name)
        
    except Exception as e:
        logger.error(f"Failed to download document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download document: {str(e)}"
        )


async def process_document_background(
    document_id: str,
    file_path: Path,
    user_id: str,
    supabase: Client
):
    """
    Background task to process document with AI extraction and transaction creation.
    
    Processing steps:
    1. Extract raw text using appropriate extractor (PDF/Image/Excel)
    2. Classify document type using AI
    3. Extract structured data using AI with document-type-specific prompts
    4. Calculate confidence scores
    5. Auto-create transaction if confidence is high enough (>0.85)
    6. Update database with results
    
    Args:
        document_id: Document ID
        file_path: Path to document file
        user_id: User ID who uploaded the document
        supabase: Supabase client
    """
    try:
        logger.info(f"Starting background processing for document {document_id}")
        
        # Update status to processing
        supabase.table("documents").update({
            "extraction_status": "processing"
        }).eq("id", document_id).execute()
        
        # STEP 1: Extract raw text using document processor
        result = document_processor.process_document(file_path, document_id=document_id)
        
        if result["status"] != "completed":
            # Text extraction failed
            supabase.table("documents").update({
                "extraction_status": "failed",
                "processing_error": result.get("error", "Text extraction failed"),
                "processed_at": datetime.utcnow().isoformat()
            }).eq("id", document_id).execute()
            logger.error(f"Text extraction failed for document {document_id}: {result.get('error')}")
            return
        
        # Get extracted text
        extraction_result = result.get("extraction_result", {})
        raw_text = extraction_result.get("raw_text", "")
        
        if not raw_text or len(raw_text.strip()) < 10:
            # Not enough text to process
            supabase.table("documents").update({
                "extraction_status": "failed",
                "processing_error": "Insufficient text extracted from document",
                "raw_text": raw_text,
                "processed_at": datetime.utcnow().isoformat()
            }).eq("id", document_id).execute()
            logger.error(f"Insufficient text extracted from document {document_id}")
            return
        
        # STEP 2: Classify document type using AI
        logger.info(f"Classifying document {document_id} using AI...")
        classification_result = document_classifier.classify_document(
            file_path=file_path,
            extracted_text=raw_text,
            structured_data=extraction_result.get("structured_data")
        )
        document_type = classification_result["document_type"]
        classification_confidence = classification_result["confidence"]
        is_multi_transaction = classification_result.get("is_multi_transaction", False)
        
        logger.info(
            f"Document {document_id} classified as '{document_type}' "
            f"with confidence {classification_confidence:.2f}, "
            f"multi-transaction: {is_multi_transaction}"
        )
        
        # STEP 3: Check if document needs chunking
        logger.info(f"Checking if document {document_id} needs chunking...")
        structured_data = extraction_result.get("structured_data", {})
        
        should_chunk = document_chunker.should_chunk_document(raw_text, structured_data)
        
        if should_chunk and is_multi_transaction:
            logger.info(f"Document {document_id} will be processed in chunks")
            chunks = document_chunker.chunk_document(raw_text, structured_data, strategy="auto")
            logger.info(f"Document split into {len(chunks)} chunks")
            
            # Estimate processing time
            est_time = document_chunker.estimate_processing_time(chunks)
            logger.info(f"Estimated processing time: {est_time:.1f} seconds")
        else:
            # Process as single document
            chunks = [{
                "chunk_id": 1,
                "chunk_type": "full_document",
                "text": raw_text,
                "structured_data": structured_data
            }]
        
        # STEP 4: Extract structured data using AI (process each chunk)
        logger.info(f"Extracting structured data from {len(chunks)} chunk(s)...")
        
        # Get business_id for category matching
        doc_response = supabase.table("documents").select("business_id").eq(
            "id", document_id
        ).execute()
        business_id = doc_response.data[0]["business_id"] if doc_response.data else None
        
        if not business_id:
            raise Exception("Could not determine business_id for document")
        
        # Process all chunks and collect extracted data
        all_extracted_data = []
        total_transactions_extracted = 0
        
        for idx, chunk in enumerate(chunks, 1):
            logger.info(f"Processing chunk {idx}/{len(chunks)}...")
            
            chunk_text = chunk.get("text", raw_text)
            chunk_structured_data = chunk.get("structured_data", structured_data)
            
            # If document is multi-transaction, force multi-transaction extraction for each chunk
            if is_multi_transaction:
                if not chunk_structured_data:
                    chunk_structured_data = {}
                # Add hint that this should extract multiple transactions
                chunk_structured_data["extraction_method"] = "multi_transaction"
                chunk_structured_data["force_multi_transaction"] = True
            
            # Extract structured data for this chunk
            chunk_extracted = data_extractor.extract(
                text=chunk_text,
                document_type=document_type,
                business_id=business_id,
                supabase_client=supabase,
                structured_data=chunk_structured_data
            )
            
            # Check if multi-transaction result
            if chunk_extracted.get("extraction_type") == "multi_transaction":
                transactions = chunk_extracted.get("transactions", [])
                total_transactions_extracted += len(transactions)
                all_extracted_data.extend(transactions)
                logger.info(f"Chunk {idx} extracted {len(transactions)} transactions")
            else:
                # Single transaction
                all_extracted_data.append(chunk_extracted)
                total_transactions_extracted += 1
                logger.info(f"Chunk {idx} extracted 1 transaction")
        
        # Combine results
        if total_transactions_extracted > 1:
            extracted_data = {
                "extraction_type": "multi_transaction",
                "total_processed_transactions": total_transactions_extracted,
                "valid_transactions": len([t for t in all_extracted_data if t.get("vendor") and t.get("amount")]),
                "transactions": all_extracted_data,
                "document_type": document_type,
                "extraction_method": "chunked_processing" if len(chunks) > 1 else "batch_processing"
            }
        else:
            extracted_data = all_extracted_data[0] if all_extracted_data else {}
        
        # STEP 5: Calculate overall confidence
        field_confidence = extracted_data.get("field_confidence", {})
        overall_confidence = confidence_scorer.calculate_overall_confidence(
            field_confidence=field_confidence,
            extracted_fields=extracted_data,
            structured_data=extraction_result  # Pass structured data for completeness scoring
        )
        
        # Get recommendation
        recommendation = confidence_scorer.get_recommendation(overall_confidence)
        
        logger.info(
            f"Data extraction complete for document {document_id}. "
            f"Overall confidence: {overall_confidence:.2f}. "
            f"Recommendation: {recommendation['action']}"
        )
        
        # STEP 6: Auto-create transaction(s) based on extraction results
        transaction_ids = []
        transactions_created = 0
        
        # Get document details for transaction creation
        doc_response = supabase.table("documents").select("business_id").eq(
            "id", document_id
        ).execute()
        
        if doc_response.data and len(doc_response.data) > 0:
            doc_data = doc_response.data[0]
            business_id_str = doc_data.get("business_id")
            
            # Get default account for the business
            account_response = supabase.table("accounts").select("id").eq(
                "business_id", business_id_str
            ).eq("is_active", True).order("is_primary", desc=True).limit(1).execute()
            
            account_id = None
            if account_response.data and len(account_response.data) > 0:
                account_id = account_response.data[0]["id"]
            
            if account_id:
                # Check if multi-transaction document
                if extracted_data.get("extraction_type") == "multi_transaction":
                    logger.info(f"Creating multiple transactions for document {document_id}...")
                    
                    created_result = await transaction_creator.create_from_document(
                        document_id=document_id,
                        business_id=business_id_str,
                        account_id=account_id,
                        user_id=user_id,
                        extracted_data=extracted_data,
                        confidence_score=overall_confidence,
                        supabase_client=supabase
                    )
                    
                    if created_result:
                        transaction_ids = created_result.get("transaction_ids", [])
                        transactions_created = created_result.get("transactions_created", 0)
                        logger.info(
                            f"✅ Created {transactions_created} transactions for document {document_id}"
                        )
                else:
                    # Single transaction
                    should_create = await transaction_creator.should_create_transaction(
                        confidence_score=overall_confidence,
                        extracted_data=extracted_data
                    )
                    
                    if should_create:
                        logger.info(f"Creating single transaction for document {document_id}...")
                        
                        created_transaction = await transaction_creator.create_from_document(
                            document_id=document_id,
                            business_id=business_id_str,
                            account_id=account_id,
                            user_id=user_id,
                            extracted_data=extracted_data,
                            confidence_score=overall_confidence,
                            supabase_client=supabase
                        )
                        
                        if created_transaction:
                            transaction_id = created_transaction.get("id")
                            if transaction_id:
                                transaction_ids.append(transaction_id)
                                transactions_created = 1
                            logger.info(
                                f"✅ Transaction {transaction_id} created for document {document_id}"
                            )
                    else:
                        logger.info(
                            f"Confidence {overall_confidence:.2f} below threshold. "
                            f"Transaction not auto-created."
                        )
            else:
                logger.warning(f"No active account found for business {business_id_str}, cannot create transactions")
        
        # STEP 7: Update document with final results
        update_data = {
            "extraction_status": "completed",
            "document_type": document_type,
            "raw_text": raw_text,
            "structured_data": extracted_data,
            "confidence_score": overall_confidence,
            "auto_created_transaction": transactions_created > 0,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        # Add transaction reference(s)
        if len(transaction_ids) == 1:
            update_data["transaction_id"] = transaction_ids[0]
        elif len(transaction_ids) > 1:
            # Store multiple transaction IDs in structured_data
            update_data["structured_data"]["transaction_ids"] = transaction_ids
            update_data["structured_data"]["transactions_created"] = transactions_created
        
        supabase.table("documents").update(update_data).eq("id", document_id).execute()
        
        logger.info(
            f"✅ Successfully processed document {document_id}. "
            f"Type: {document_type}, Confidence: {overall_confidence:.2f}, "
            f"Transactions created: {transactions_created}, "
            f"Multi-transaction: {extracted_data.get('extraction_type') == 'multi_transaction'}"
        )
        
    except Exception as e:
        logger.error(f"Background processing exception for document {document_id}: {str(e)}")
        
        # Update with error
        try:
            supabase.table("documents").update({
                "extraction_status": "failed",
                "processing_error": str(e),
                "processed_at": datetime.utcnow().isoformat()
            }).eq("id", document_id).execute()
        except Exception as update_error:
            logger.error(f"Failed to update error status: {str(update_error)}")
    
    finally:
        # Clean up temporary file
        try:
            if file_path.exists():
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up temporary file: {str(cleanup_error)}")


@router.post("/{document_id}/process", response_model=Dict[str, Any])
async def process_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Trigger document processing (text extraction).
    
    Processes document in background and updates extraction_status.
    Requires member or higher role.
    """
    try:
        # Verify access and get document
        document = await verify_document_access(
            str(document_id),
            current_user,
            supabase,
            required_role="member"
        )
        
        # Check if already processing
        current_status = document.get("extraction_status", "pending")
        if current_status == "processing":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document is already being processed"
            )
        
        # Get storage path
        storage_path = document.get("file_path")  # Changed from storage_path to file_path
        if not storage_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has no storage path"
            )
        
        # Download document
        file_path = await download_document_from_storage(
            str(document_id),
            storage_path,
            supabase
        )
        
        # Add background task
        background_tasks.add_task(
            process_document_background,
            str(document_id),
            file_path,
            current_user.get("user_id"),
            supabase
        )
        
        return {
            "message": "Document processing started",
            "document_id": str(document_id),
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting document processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start processing: {str(e)}"
        )


@router.get("/{document_id}/status", response_model=Dict[str, Any])
async def get_processing_status(
    document_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get document processing status.
    
    Returns extraction status, raw text preview, and structured data.
    Requires member or higher role.
    """
    try:
        # Verify access and get document with processing data
        response = supabase.table("documents").select(
            "id, document_name, business_id, extraction_status, document_type, "
            "raw_text, structured_data, confidence_score, processing_error, "
            "processed_at, created_at, transaction_id, auto_created_transaction"
        ).eq("id", str(document_id)).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        document = response.data[0]
        
        # Verify access (this will check business membership)
        await verify_document_access(
            str(document_id),
            current_user,
            supabase,
            required_role="member"
        )
        
        # Build response
        status_response = {
            "document_id": document["id"],
            "document_name": document["document_name"],
            "extraction_status": document.get("extraction_status", "pending"),
            "document_type": document.get("document_type"),
            "confidence_score": document.get("confidence_score"),
            "processing_error": document.get("processing_error"),
            "processed_at": document.get("processed_at"),
            "created_at": document.get("created_at"),
            "transaction_id": document.get("transaction_id"),
            "auto_created_transaction": document.get("auto_created_transaction", False)
        }
        
        # Add text preview if available
        raw_text = document.get("raw_text")
        if raw_text:
            status_response["raw_text_preview"] = raw_text[:500]  # First 500 chars
            status_response["raw_text_length"] = len(raw_text)
            status_response["word_count"] = len(raw_text.split())
        
        # Add structured data if available
        structured_data = document.get("structured_data")
        if structured_data:
            status_response["structured_data"] = structured_data
        
        return status_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/supported-types", response_model=Dict[str, Any])
async def get_supported_types(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get list of supported file types for processing.
    
    Returns supported extensions and MIME types.
    """
    return {
        "supported_extensions": document_processor.get_supported_extensions(),
        "supported_mimetypes": document_processor.get_supported_mimetypes(),
        "extractors": document_processor.get_extractor_info()
    }
# Trigger reload
