"""
Test script to process a specific document from Supabase
Downloads the document and runs it through the DocumentProcessor
"""
import sys
import os
from pathlib import Path
import tempfile
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.document_processor import DocumentProcessor
from app.db.supabase import get_supabase_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def process_document_from_supabase(document_id: str):
    """Process a document from Supabase Storage"""
    print("=" * 70)
    print("DOCUMENT PROCESSING TEST - FROM SUPABASE")
    print("=" * 70)
    print()
    
    # Initialize
    processor = DocumentProcessor()
    supabase = get_supabase_client()
    
    print(f"📄 Document ID: {document_id}")
    print()
    
    try:
        # Step 1: Get document info from database
        print("1️⃣  Fetching document from database...")
        response = supabase.table("documents").select("*").eq("id", document_id).execute()
        
        if not response.data or len(response.data) == 0:
            print("❌ Document not found in database")
            return
        
        document = response.data[0]
        print(f"   ✅ Found: {document['document_name']}")
        print(f"   📁 File path: {document['file_path']}")
        print(f"   📊 Current status: {document.get('extraction_status', 'N/A')}")
        print()
        
        # Step 2: Download from Supabase Storage
        print("2️⃣  Downloading from Supabase Storage...")
        file_path_in_storage = document['file_path']
        
        try:
            file_data = supabase.storage.from_("documents").download(file_path_in_storage)
            print(f"   ✅ Downloaded {len(file_data)} bytes")
        except Exception as e:
            print(f"   ❌ Download failed: {str(e)}")
            return
        
        # Step 3: Save to temporary file
        print("3️⃣  Saving to temporary file...")
        file_ext = Path(document['document_name']).suffix
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_ext,
            prefix=f"doc_{document_id}_"
        )
        temp_file.write(file_data)
        temp_file.close()
        temp_path = Path(temp_file.name)
        print(f"   ✅ Saved to: {temp_path}")
        print()
        
        # Step 4: Update status to processing
        print("4️⃣  Updating status to 'processing'...")
        supabase.table("documents").update({
            "extraction_status": "processing"
        }).eq("id", document_id).execute()
        print("   ✅ Status updated")
        print()
        
        # Step 5: Process document
        print("5️⃣  Processing document...")
        print("-" * 70)
        result = processor.process_document(temp_path, document_id=document_id)
        print("-" * 70)
        print()
        
        # Step 6: Display results
        print("6️⃣  Processing Results:")
        print(f"   Status: {result['status']}")
        print(f"   Extractor: {result.get('extractor_used', 'N/A')}")
        print(f"   Processing time: {result.get('processing_time_ms', 'N/A')}ms")
        
        if result['status'] == 'completed':
            extraction = result.get('extraction_result', {})
            print(f"   ✅ SUCCESS!")
            print(f"   📝 Text extracted: {extraction.get('text_length', 0)} characters")
            print(f"   📊 Word count: {extraction.get('word_count', 0)} words")
            print()
            
            # Show text preview
            raw_text = extraction.get('raw_text', '')
            print("   📄 TEXT PREVIEW (first 300 chars):")
            print(f"   {raw_text[:300]}...")
            print()
            
            # Show metadata
            metadata = extraction.get('metadata', {})
            print("   📋 METADATA:")
            for key, value in list(metadata.items())[:5]:
                print(f"      {key}: {value}")
            print()
            
            # Show structured data
            structured = extraction.get('structured_data', {})
            print("   📦 STRUCTURED DATA:")
            for key, value in structured.items():
                if key not in ['tables', 'records']:
                    print(f"      {key}: {value}")
            print()
            
            # Step 7: Save to database
            print("7️⃣  Saving results to database...")
            update_data = {
                "extraction_status": "completed",
                "raw_text": raw_text,
                "structured_data": structured,
                "processed_at": datetime.utcnow().isoformat()
            }
            supabase.table("documents").update(update_data).eq("id", document_id).execute()
            print("   ✅ Results saved to database")
            
        else:
            print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
            print()
            
            # Save error to database
            print("7️⃣  Saving error to database...")
            supabase.table("documents").update({
                "extraction_status": "failed",
                "processing_error": result.get('error', 'Unknown error'),
                "processed_at": datetime.utcnow().isoformat()
            }).eq("id", document_id).execute()
            print("   ✅ Error saved to database")
        
        print()
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup temp file
        try:
            if temp_path.exists():
                os.unlink(temp_path)
                print(f"🧹 Cleaned up temporary file")
        except:
            pass
    
    print()
    print("=" * 70)
    print("✅ TEST COMPLETE")
    print()
    print("📊 Check database to see results:")
    print(f"   SELECT * FROM documents WHERE id = '{document_id}';")
    print("=" * 70)


if __name__ == "__main__":
    # Your document ID
    document_id = "856e66f3-0a67-4152-8f6f-a00472371903"
    
    process_document_from_supabase(document_id)
