"""
Test image processing with database integration
Creates a receipt image, adds it to database, and processes it
"""
import sys
from pathlib import Path
from datetime import datetime
import uuid

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.document_processor import DocumentProcessor
from app.db.supabase import get_supabase_client
from PIL import Image, ImageDraw, ImageFont
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_receipt_image():
    """Create a test receipt image"""
    print("📝 Creating test receipt image...")
    
    # Create image
    img = Image.new('RGB', (600, 800), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_normal = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_normal = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    y = 50
    
    # Store name
    draw.text((180, y), "OFFICE DEPOT", fill='black', font=font_large)
    y += 40
    draw.text((150, y), "456 Business Ave, Chicago, IL 60601", fill='black', font=font_small)
    y += 30
    draw.text((200, y), "Tel: (312) 555-0123", fill='black', font=font_small)
    y += 50
    
    # Receipt info
    draw.text((50, y), "Receipt #: ODT-2025-100723", fill='black', font=font_normal)
    y += 30
    draw.text((50, y), "Date: October 7, 2025, 3:45 PM", fill='black', font=font_normal)
    y += 30
    draw.text((50, y), "Cashier: Sarah M.", fill='black', font=font_normal)
    y += 50
    
    # Items
    draw.text((50, y), "ITEMS PURCHASED:", fill='black', font=font_normal)
    y += 30
    draw.line([(50, y), (550, y)], fill='black', width=1)
    y += 20
    
    items = [
        ("HP Laser Printer Paper", "$24.99"),
        ("Stapler Heavy Duty", "$18.50"),
        ("File Folders (25 pack)", "$12.99"),
        ("Whiteboard Markers (8pk)", "$16.75"),
        ("USB Flash Drive 64GB", "$29.99"),
    ]
    
    for item, price in items:
        draw.text((50, y), item, fill='black', font=font_normal)
        draw.text((450, y), price, fill='black', font=font_normal)
        y += 28
    
    y += 20
    draw.line([(50, y), (550, y)], fill='black', width=1)
    y += 30
    
    # Totals
    draw.text((300, y), "Subtotal:", fill='black', font=font_normal)
    draw.text((450, y), "$103.22", fill='black', font=font_normal)
    y += 30
    
    draw.text((300, y), "Tax (9.5%):", fill='black', font=font_normal)
    draw.text((450, y), "$9.81", fill='black', font=font_normal)
    y += 30
    
    draw.line([(300, y), (550, y)], fill='black', width=2)
    y += 30
    
    draw.text((300, y), "TOTAL:", fill='black', font=font_large)
    draw.text((430, y), "$113.03", fill='black', font=font_large)
    y += 50
    
    # Payment
    draw.text((50, y), "Payment: Mastercard ****5678", fill='black', font=font_small)
    y += 30
    draw.text((50, y), "Approval Code: 123456", fill='black', font=font_small)
    y += 50
    
    draw.text((150, y), "Thank you for shopping at Office Depot!", fill='black', font=font_normal)
    y += 30
    draw.text((180, y), "Save your receipt for returns", fill='black', font=font_small)
    
    # Save
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='office_receipt_')
    img.save(temp_file.name, 'PNG')
    temp_file.close()
    
    print(f"   ✅ Created: {temp_file.name}")
    return Path(temp_file.name)


def test_image_with_database():
    """Test complete image processing pipeline with database"""
    print("=" * 70)
    print("IMAGE PROCESSING - FULL DATABASE INTEGRATION TEST")
    print("=" * 70)
    print()
    
    # Initialize
    processor = DocumentProcessor(tesseract_path=r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    supabase = get_supabase_client()
    
    # Create test image
    image_path = create_receipt_image()
    print()
    
    # Create document record
    print("1️⃣  Creating document record in database...")
    document_id = str(uuid.uuid4())
    document_name = "office_depot_receipt.png"
    
    # Note: We're not actually uploading to storage, just testing extraction
    document_data = {
        "id": document_id,
        "business_id": "5021efe2-7c63-4bcd-bd2b-3e243e8a4935",  # Your business ID
        "document_name": document_name,
        "file_path": f"test/{document_id}.png",  # Fake path for testing
        "file_size": image_path.stat().st_size,
        "mime_type": "image/png",
        "document_type": "receipt",
        "extraction_status": "pending"
    }
    
    try:
        supabase.table("documents").insert(document_data).execute()
        print(f"   ✅ Document created: {document_id}")
        print(f"   📄 Name: {document_name}")
    except Exception as e:
        print(f"   ⚠️  Insert failed (may already exist): {e}")
    print()
    
    # Update to processing
    print("2️⃣  Updating status to 'processing'...")
    supabase.table("documents").update({
        "extraction_status": "processing"
    }).eq("id", document_id).execute()
    print("   ✅ Status updated")
    print()
    
    # Process image
    print("3️⃣  Processing image with OCR...")
    print("-" * 70)
    result = processor.process_document(image_path, document_id=document_id)
    print("-" * 70)
    print()
    
    # Display results
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
        print(f"   🎯 Confidence: {extraction.get('structured_data', {}).get('confidence_score', 'N/A')}")
        print()
        
        # Show extracted text
        raw_text = extraction.get('raw_text', '')
        print("   📄 EXTRACTED TEXT:")
        print("   " + "-" * 66)
        for line in raw_text.split('\n'):
            print(f"   {line}")
        print("   " + "-" * 66)
        print()
        
        # Save to database
        print("5️⃣  Saving results to database...")
        structured_data = extraction.get('structured_data', {})
        update_data = {
            "extraction_status": "completed",
            "raw_text": raw_text,
            "structured_data": structured_data,
            "confidence_score": structured_data.get('confidence_score'),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("documents").update(update_data).eq("id", document_id).execute()
        print("   ✅ Results saved to database")
        print()
        
        # Verify
        print("6️⃣  Verifying in database...")
        verify = supabase.table("documents").select(
            "extraction_status, confidence_score, LENGTH(raw_text) as text_length"
        ).eq("id", document_id).execute()
        
        if verify.data:
            v = verify.data[0]
            print(f"   ✅ Status: {v.get('extraction_status')}")
            print(f"   ✅ Confidence: {v.get('confidence_score')}")
            print(f"   ✅ Text length: {v.get('text_length')} chars")
        print()
        
    else:
        print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
        
        # Save error
        supabase.table("documents").update({
            "extraction_status": "failed",
            "processing_error": result.get('error'),
            "processed_at": datetime.utcnow().isoformat()
        }).eq("id", document_id).execute()
    
    # Cleanup
    import os
    try:
        os.unlink(image_path)
        print("🧹 Cleaned up temporary image file")
    except:
        pass
    
    print()
    print("=" * 70)
    print("✅ IMAGE PROCESSING TEST COMPLETE")
    print()
    print(f"📊 View results in database:")
    print(f"   SELECT * FROM documents WHERE id = '{document_id}';")
    print("=" * 70)


if __name__ == "__main__":
    test_image_with_database()
