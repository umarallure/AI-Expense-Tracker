from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.schemas.document import DocumentCreate, DocumentResponse
from app.services.ai_extractor import DocumentExtractor
from app.db.supabase import supabase_client

router = APIRouter()

@router.post("/", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.content_type in ["application/pdf", "image/jpeg", "image/png", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"]:
        raise HTTPException(status_code=400, detail="Invalid file type.")
    
    # Save the file to Supabase Storage
    file_path = f"documents/{file.filename}"
    await supabase_client.storage.from_("documents").upload(file_path, file.file)
    
    # Process the document
    extractor = DocumentExtractor()
    document_text = await extractor.extract_text(file.file)
    transactions = await extractor.extract_transactions(document_text)
    
    # Save document metadata and transactions to the database
    document_data = DocumentCreate(file_path=file_path, transactions=transactions)
    document_id = await supabase_client.from_("documents").insert(document_data.dict()).execute()
    
    return {"id": document_id, "file_path": file_path, "transactions": transactions}

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    document = await supabase_client.from_("documents").select("*").eq("id", document_id).single().execute()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    return document

@router.delete("/{document_id}", response_model=dict)
async def delete_document(document_id: str):
    result = await supabase_client.from_("documents").delete().eq("id", document_id).execute()
    if result["count"] == 0:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    return {"detail": "Document deleted successfully."}