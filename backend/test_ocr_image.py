"""
Test Tesseract OCR with ImageExtractor
Creates a test image with text and processes it
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.extractors import ImageExtractor
from PIL import Image, ImageDraw, ImageFont
import tempfile


def create_test_receipt_image():
    """Create a simple receipt image for testing"""
    print("📝 Creating test receipt image...")
    
    # Create a white image
    img = Image.new('RGB', (600, 800), color='white')
    draw = ImageDraw.Draw(img)
    
    # Use default font (may not be perfect but works)
    try:
        # Try to use a TrueType font if available
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_normal = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        # Fallback to default
        font_large = ImageFont.load_default()
        font_normal = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw receipt content
    y = 50
    
    # Header
    draw.text((200, y), "ACME STORE", fill='black', font=font_large)
    y += 40
    draw.text((150, y), "123 Main Street, City, ST 12345", fill='black', font=font_small)
    y += 30
    draw.text((200, y), "Tel: (555) 123-4567", fill='black', font=font_small)
    y += 50
    
    # Receipt details
    draw.text((50, y), "Receipt #: 2025-10-07-001", fill='black', font=font_normal)
    y += 30
    draw.text((50, y), "Date: October 7, 2025", fill='black', font=font_normal)
    y += 30
    draw.text((50, y), "Time: 2:30 PM", fill='black', font=font_normal)
    y += 50
    
    # Line items
    draw.text((50, y), "ITEMS:", fill='black', font=font_normal)
    y += 30
    draw.line([(50, y), (550, y)], fill='black', width=1)
    y += 20
    
    items = [
        ("Office Supplies", "$45.99"),
        ("Printer Paper", "$12.50"),
        ("Pens (Box of 12)", "$8.75"),
        ("Notebooks (3 pack)", "$15.00"),
    ]
    
    for item, price in items:
        draw.text((50, y), item, fill='black', font=font_normal)
        draw.text((450, y), price, fill='black', font=font_normal)
        y += 30
    
    y += 20
    draw.line([(50, y), (550, y)], fill='black', width=1)
    y += 30
    
    # Totals
    draw.text((300, y), "Subtotal:", fill='black', font=font_normal)
    draw.text((450, y), "$82.24", fill='black', font=font_normal)
    y += 30
    
    draw.text((300, y), "Tax (8.5%):", fill='black', font=font_normal)
    draw.text((450, y), "$6.99", fill='black', font=font_normal)
    y += 30
    
    draw.line([(300, y), (550, y)], fill='black', width=2)
    y += 30
    
    draw.text((300, y), "TOTAL:", fill='black', font=font_large)
    draw.text((450, y), "$89.23", fill='black', font=font_large)
    y += 50
    
    # Footer
    draw.text((150, y), "Payment Method: Visa ending in 4567", fill='black', font=font_small)
    y += 30
    draw.text((200, y), "Thank you for your business!", fill='black', font=font_normal)
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='receipt_test_')
    img.save(temp_file.name, 'PNG')
    temp_file.close()
    
    print(f"   ✅ Created: {temp_file.name}")
    return Path(temp_file.name)


def test_image_extractor():
    """Test ImageExtractor with OCR"""
    print("=" * 70)
    print("IMAGE EXTRACTOR TEST - OCR")
    print("=" * 70)
    print()
    
    # Create test image
    test_image_path = create_test_receipt_image()
    print()
    
    # Initialize extractor with explicit Tesseract path
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    extractor = ImageExtractor(tesseract_path=tesseract_path)
    
    print(f"📷 Extractor: {extractor.name}")
    print(f"   Supported: {extractor.SUPPORTED_EXTENSIONS}")
    print(f"   Tesseract: {tesseract_path}")
    print()
    
    # Extract text
    print("🔍 Processing image with OCR...")
    print("-" * 70)
    result = extractor.extract_safe(test_image_path)
    print("-" * 70)
    print()
    
    if result.success:
        print("✅ OCR Extraction Successful!")
        print()
        
        # Metadata
        print("📋 IMAGE METADATA:")
        for key, value in result.metadata.items():
            print(f"   {key}: {value}")
        print()
        
        # Structured data
        print("📦 STRUCTURED DATA:")
        for key, value in result.structured_data.items():
            print(f"   {key}: {value}")
        print()
        
        # Extracted text
        print("📝 EXTRACTED TEXT:")
        print("-" * 70)
        print(result.raw_text)
        print("-" * 70)
        print()
        
        print(f"📊 STATS:")
        print(f"   Total characters: {len(result.raw_text)}")
        print(f"   Word count: {len(result.raw_text.split())}")
        print(f"   Confidence score: {result.structured_data.get('confidence_score', 'N/A')}")
        
    else:
        print(f"❌ OCR Extraction Failed!")
        print(f"   Error: {result.error}")
    
    print()
    print("=" * 70)
    print()
    
    # Cleanup
    import os
    try:
        os.unlink(test_image_path)
        print("🧹 Cleaned up test image")
    except:
        pass
    
    return result


if __name__ == "__main__":
    test_image_extractor()
