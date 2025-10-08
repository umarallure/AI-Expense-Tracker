"""
Document management endpoints for uploading and managing business documents.
Handles document CRUD operations and Supabase Storage integration.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from loguru import logger
from typing import Dict, Any, List, Optional
from uuid import uuid4, UUID
from datetime import datetime
import os
import mimetypes

from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    Document,
    DocumentList,
    DocumentUploadResponse
)
from app.schemas.auth import MessageResponse
from app.core.security import get_current_user
from app.core.deps import check_business_permission
from app.db.supabase import get_supabase_client
from supabase import Client

router = APIRouter(prefix="/documents", tags=["Documents"])

# Allowed file types and max size
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.xlsx', '.xls', '.csv', '.doc', '.docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded file"""
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, "Valid"


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    business_id: str = Form(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    transaction_id: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Upload a document to Supabase Storage.
    
    Requires member or higher role.
    """
    # Manually check business access since business_id comes from Form, not Query
    from app.core.deps import get_business_access
    business_access = await get_business_access(business_id, current_user, supabase)
    
    # Check permission
    role = business_access.get("role", "viewer")
    permission_levels = {"owner": 4, "admin": 3, "accountant": 2, "member": 2, "viewer": 1}
    user_level = permission_levels.get(role, 0)
    required_level = permission_levels.get("member", 0)
    
    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Required: member"
        )
    try:
        # Validate file
        is_valid, error_message = validate_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Generate unique filename
        document_id = str(uuid4())
        file_ext = os.path.splitext(file.filename)[1].lower()
        storage_filename = f"{business_id}/{document_id}{file_ext}"
        
        # Get MIME type
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
        
        # Upload to Supabase Storage
        try:
            storage_response = supabase.storage.from_('documents').upload(
                path=storage_filename,
                file=file_content,
                file_options={
                    "content-type": mime_type,
                    "cache-control": "3600",
                    "upsert": "false"
                }
            )
        except Exception as storage_error:
            logger.error(f"Storage upload error: {storage_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to storage: {str(storage_error)}"
            )
        
        # Parse tags if provided
        tags_list = [tag.strip() for tag in tags.split(',')] if tags else None
        
        # Create document record in database
        document_data = {
            "id": document_id,
            "business_id": business_id,
            "transaction_id": transaction_id if transaction_id else None,
            "user_id": str(current_user["user_id"]),
            "document_name": file.filename,
            "document_type": document_type,
            "file_path": storage_filename,
            "file_size": file_size,
            "mime_type": mime_type,
            "storage_bucket": "documents",
            "description": description,
            "tags": tags_list,
            "metadata": {
                "original_filename": file.filename,
                "uploaded_by": current_user.get("email", ""),
            },
            "is_processed": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("documents").insert(document_data).execute()
        
        if not result.data:
            # Cleanup: delete uploaded file if database insert fails
            try:
                supabase.storage.from_('documents').remove([storage_filename])
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save document metadata"
            )
        
        created_document = result.data[0]
        
        return DocumentUploadResponse(
            id=created_document["id"],
            document_name=created_document["document_name"],
            file_path=created_document["file_path"],
            file_size=created_document["file_size"],
            mime_type=created_document["mime_type"],
            created_at=created_document["created_at"],
            message="Document uploaded successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/", response_model=DocumentList)
async def get_documents(
    business_id: str = Query(..., description="Business ID to filter documents"),
    transaction_id: Optional[str] = Query(None, description="Filter by transaction ID"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    business_access: Dict = Depends(check_business_permission("member")),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get documents for a business with optional filters.
    
    Requires member or higher role.
    """
    try:
        # Build query
        query = supabase.table("documents").select("*").eq("business_id", business_id)
        
        if transaction_id:
            query = query.eq("transaction_id", transaction_id)
        
        if document_type:
            query = query.eq("document_type", document_type)
        
        # Apply pagination
        result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        
        # Get total count
        count_query = supabase.table("documents").select("*", count="exact").eq("business_id", business_id)
        if transaction_id:
            count_query = count_query.eq("transaction_id", transaction_id)
        if document_type:
            count_query = count_query.eq("document_type", document_type)
        
        count_result = count_query.execute()
        total = count_result.count
        
        documents = [Document(**item) for item in result.data]
        
        return DocumentList(documents=documents, total=total)
    
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get a specific document by ID.
    
    Requires member or higher role.
    """
    try:
        result = supabase.table("documents").select("*").eq("id", document_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        document = result.data[0]
        
        # Check if user has access to this business
        business_response = supabase.table("business_members").select("*").eq(
            "business_id", document["business_id"]
        ).eq("user_id", current_user["user_id"]).eq("status", "active").execute()
        
        if not business_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this document"
            )
        
        return Document(**document)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch document: {str(e)}"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get a signed URL to download the document.
    
    Requires member or higher role.
    """
    try:
        # Get document metadata
        result = supabase.table("documents").select("*").eq("id", document_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        document = result.data[0]
        
        # Check if user has access to this business
        business_response = supabase.table("business_members").select("*").eq(
            "business_id", document["business_id"]
        ).eq("user_id", current_user["user_id"]).eq("status", "active").execute()
        
        if not business_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this document"
            )
        
        # Generate signed URL (valid for 1 hour)
        try:
            signed_url = supabase.storage.from_('documents').create_signed_url(
                path=document["file_path"],
                expires_in=3600
            )
            
            return {
                "download_url": signed_url['signedURL'],
                "expires_in": 3600,
                "document_name": document["document_name"]
            }
        except Exception as storage_error:
            logger.error(f"Storage download error: {storage_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate download URL"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@router.put("/{document_id}", response_model=Document)
async def update_document(
    document_id: str,
    document_data: DocumentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update document metadata.
    
    Users can edit their own documents or admins can edit any document.
    """
    try:
        # Check if document exists
        existing = supabase.table("documents").select("*").eq("id", document_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        document = existing.data[0]
        business_id = document["business_id"]
        
        # Check business access
        business_response = supabase.table("business_members").select("*").eq(
            "business_id", business_id
        ).eq("user_id", current_user["user_id"]).eq("status", "active").execute()
        
        if not business_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this business"
            )
        
        member = business_response.data[0]
        user_role = member.get("role", "viewer")
        user_id = str(current_user["user_id"])
        document_user_id = document.get("user_id")
        
        # Allow editing if user is admin/owner OR user created the document
        can_edit = (user_role in ["admin", "owner"] or document_user_id == user_id)
        
        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own documents, or you need admin permissions"
            )
        
        # Update document
        update_dict = document_data.model_dump(exclude_unset=True)
        
        # Convert UUID objects to strings for Supabase
        if "transaction_id" in update_dict and update_dict["transaction_id"]:
            update_dict["transaction_id"] = str(update_dict["transaction_id"])
        
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        result = supabase.table("documents").update(update_dict).eq("id", document_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update document"
            )
        
        return Document(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )


@router.delete("/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Delete a document and its file from storage.
    
    Users can delete their own documents or admins can delete any document.
    """
    try:
        # Check if document exists
        existing = supabase.table("documents").select("*").eq("id", document_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        document = existing.data[0]
        business_id = document["business_id"]
        
        # Check business access
        business_response = supabase.table("business_members").select("*").eq(
            "business_id", business_id
        ).eq("user_id", current_user["user_id"]).eq("status", "active").execute()
        
        if not business_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this business"
            )
        
        member = business_response.data[0]
        user_role = member.get("role", "viewer")
        user_id = str(current_user["user_id"])
        document_user_id = document.get("user_id")
        
        # Allow deletion if user is admin/owner OR user created the document
        can_delete = (user_role in ["admin", "owner"] or document_user_id == user_id)
        
        if not can_delete:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own documents, or you need admin permissions"
            )
        
        # Delete file from storage
        try:
            supabase.storage.from_('documents').remove([document["file_path"]])
        except Exception as storage_error:
            logger.warning(f"Failed to delete file from storage: {storage_error}")
            # Continue with database deletion even if storage deletion fails
        
        # Delete document record from database
        supabase.table("documents").delete().eq("id", document_id).execute()
        
        return MessageResponse(message="Document deleted successfully")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )