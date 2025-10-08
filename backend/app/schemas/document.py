from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class DocumentBase(BaseModel):
    business_id: UUID
    transaction_id: Optional[UUID] = None
    document_name: str
    document_type: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    document_name: Optional[str] = None
    document_type: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    transaction_id: Optional[UUID] = None

class Document(DocumentBase):
    id: UUID
    user_id: UUID
    file_path: str
    file_size: int
    mime_type: str
    storage_bucket: str
    metadata: Optional[dict] = None
    is_processed: bool
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # Phase 3.2: Document Processing fields
    extraction_status: Optional[str] = None
    raw_text: Optional[str] = None
    structured_data: Optional[dict] = None
    confidence_score: Optional[float] = None
    processing_error: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True

class DocumentList(BaseModel):
    documents: List[Document]
    total: int

class DocumentUploadResponse(BaseModel):
    id: UUID
    document_name: str
    file_path: str
    file_size: int
    mime_type: str
    created_at: datetime
    message: str