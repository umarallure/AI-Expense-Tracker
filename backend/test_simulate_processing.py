"""
Test script to simulate document processing and update database
Uses local sample file to demonstrate the full pipeline
"""
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.document_processor import DocumentProcessor
from app.db.supabase import get_supabase_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def simulate_document_processing(document_id: str, local_file_path: str):
    """Simulate processing with local file and update database"""
    print("=" * 70)
    print("DOCUMENT PROCESSING SIMULATION")
    print("=" * 70)
    print()
    
    # Initialize
    processor = DocumentProcessor()
    supabase = get_supabase_client()
    
    print(f"📄 Document ID: {document_id}")
    print(f"📁 Local file: {local_file_path}")
    print()
    
    try:
        # Step 1: Verify document exists in database
        print("1️⃣  Fetching document from database...")
        response = supabase.table("documents").select("*").eq("id", document_id).execute()
        
        if not response.data or len(response.data) == 0:
            print("❌ Document not found in database")
            return
        
        document = response.data[0]
        print(f"   ✅ Found: {document['document_name']}")
        print(f"   📊 Current status: {document.get('extraction_status', 'N/A')}")
        print()
        
        # Step 2: Update status to processing
        print("2️⃣  Updating status to 'processing'...")
        supabase.table("documents").update({
            "extraction_status": "processing"
        }).eq("id", document_id).execute()
        print("   ✅ Status updated")
        print()
        
        # Step 3: Process local file
        print("3️⃣  Processing document with DocumentProcessor...")
        print("-" * 70)
        file_path = Path(local_file_path)
        
        if not file_path.exists():
            print(f"   ❌ File not found: {file_path}")
            return
        
        result = processor.process_document(file_path, document_id=document_id)
        print("-" * 70)
        print()
        
        # Step 4: Display results
        print("4️⃣  Processing Results:")
        print(f"   Status: {result['status']}")
        print(f"   Extractor: {result.get('extractor_used', 'N/A')}")
        print(f"   Processing time: {result.get('processing_time_ms', 'N/A')}ms")
        print()
        
        if result['status'] == 'completed':
            extraction = result.get('extraction_result', {})
            print(f"   ✅ SUCCESS!")
            print(f"   📝 Text extracted: {extraction.get('text_length', 0)} characters")
            print(f"   📊 Word count: {extraction.get('word_count', 0)} words")
            print()
            
            # Show text preview
            raw_text = extraction.get('raw_text', '')
            print("   📄 TEXT PREVIEW (first 500 chars):")
            preview = raw_text[:500].replace('\n', ' ')
            print(f"   {preview}...")
            print()
            
            # Show metadata
            metadata = extraction.get('metadata', {})
            print("   📋 METADATA:")
            for key, value in list(metadata.items())[:6]:
                print(f"      {key}: {value}")
            print()
            
            # Show structured data
            structured = extraction.get('structured_data', {})
            print("   📦 STRUCTURED DATA:")
            for key, value in structured.items():
                if key not in ['tables', 'records']:
                    print(f"      {key}: {value}")
            print()
            
            # Step 5: Save to database
            print("5️⃣  Saving results to database...")
            update_data = {
                "extraction_status": "completed",
                "raw_text": raw_text,
                "structured_data": structured,
                "processed_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("documents").update(update_data).eq("id", document_id).execute()
            print("   ✅ Results saved successfully!")
            print()
            
            # Step 6: Verify in database
            print("6️⃣  Verifying database update...")
            verify_response = supabase.table("documents").select(
                "extraction_status, document_type, processed_at"
            ).eq("id", document_id).execute()
            
            if verify_response.data:
                verified = verify_response.data[0]
                print(f"   ✅ Status: {verified.get('extraction_status')}")
                print(f"   ✅ Processed at: {verified.get('processed_at')}")
            print()
            
        else:
            print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
            print()
            
            # Save error to database
            print("5️⃣  Saving error to database...")
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
        
        # Update database with error
        try:
            supabase.table("documents").update({
                "extraction_status": "failed",
                "processing_error": str(e),
                "processed_at": datetime.utcnow().isoformat()
            }).eq("id", document_id).execute()
        except:
            pass
    
    print()
    print("=" * 70)
    print("✅ SIMULATION COMPLETE")
    print()
    print("📊 View results in database:")
    print(f"   SELECT extraction_status, LENGTH(raw_text), structured_data")
    print(f"   FROM documents WHERE id = '{document_id}';")
    print("=" * 70)


if __name__ == "__main__":
    # Your document ID from database
    document_id = "856e66f3-0a67-4152-8f6f-a00472371903"
    
    # Use local sample file (same PDF we've been testing with)
    local_file = "sample_invoice.pdf"
    
    simulate_document_processing(document_id, local_file)
