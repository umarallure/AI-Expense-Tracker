from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentBase(BaseModel):
    user_id: str
    document_type: str
    upload_timestamp: datetime
    original_filename: str
    size: int
    metadata: Optional[dict] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(DocumentBase):
    pass

class Document(DocumentBase):
    id: str

    class Config:
        orm_mode = True