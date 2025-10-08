"""
Test script for PDFExtractor
Run this to verify PDF extraction is working correctly.
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.extractors import PDFExtractor


def test_pdf_extractor():
    """Test PDF extraction"""
    print("=" * 60)
    print("PDF EXTRACTOR TEST")
    print("=" * 60)
    
    # Initialize extractor
    extractor = PDFExtractor()
    print(f"✅ Initialized: {extractor}")
    print(f"   Supported extensions: {extractor.SUPPORTED_EXTENSIONS}")
    print(f"   Supported MIME types: {extractor.SUPPORTED_MIMETYPES}")
    print()
    
    # Test with a sample PDF (you'll need to provide one)
    print("To test PDF extraction:")
    print("1. Place a PDF file in the backend folder")
    print("2. Update the file path below")
    print("3. Run this script again")
    print()
    
    # Example usage
    test_pdf_path = Path("sample_invoice.pdf")  # Change this to your PDF
    
    if test_pdf_path.exists():
        print(f"📄 Testing with: {test_pdf_path.name}")
        print("-" * 60)
        
        # Extract
        result = extractor.extract_safe(test_pdf_path)
        
        if result.success:
            print("✅ Extraction successful!")
            print()
            print("METADATA:")
            for key, value in result.metadata.items():
                print(f"  {key}: {value}")
            print()
            
            print("STRUCTURED DATA:")
            for key, value in result.structured_data.items():
                if key != "tables":  # Don't print full tables
                    print(f"  {key}: {value}")
            print()
            
            print("EXTRACTED TEXT (first 500 chars):")
            print(result.raw_text[:500])
            if len(result.raw_text) > 500:
                print(f"... ({len(result.raw_text)} total characters)")
            print()
            
            if result.structured_data.get("tables"):
                print(f"📊 Found {len(result.structured_data['tables'])} table(s)")
                for table in result.structured_data['tables']:
                    print(f"   Table {table['table_number']} on page {table['page']}: "
                          f"{len(table['headers'])} columns, {table['row_count']} rows")
        else:
            print(f"❌ Extraction failed: {result.error}")
    else:
        print(f"⚠️  File not found: {test_pdf_path}")
        print("   Please create a sample PDF file to test with.")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    test_pdf_extractor()
