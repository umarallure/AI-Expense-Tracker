"""
Test script for all document extractors
Run this to verify PDF, Image, and Excel extraction is working correctly.
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.extractors import PDFExtractor, ImageExtractor, ExcelExtractor


def test_all_extractors():
    """Test all document extractors"""
    print("=" * 70)
    print("DOCUMENT EXTRACTORS TEST SUITE")
    print("=" * 70)
    print()
    
    # Test configurations
    test_files = {
        "PDF": {
            "extractor": PDFExtractor(),
            "file": "sample_invoice.pdf",
            "icon": "📄"
        },
        "Image (OCR)": {
            "extractor": ImageExtractor(),
            "file": "sample_receipt.jpg",  # or .png
            "icon": "🖼️"
        },
        "Excel/CSV": {
            "extractor": ExcelExtractor(),
            "file": "sample_expenses.xlsx",  # or .csv
            "icon": "📊"
        }
    }
    
    results = {}
    
    # Test each extractor
    for test_name, config in test_files.items():
        print(f"{config['icon']} Testing {test_name} Extractor")
        print("-" * 70)
        
        extractor = config['extractor']
        file_path = Path(config['file'])
        
        print(f"   Extractor: {extractor.name}")
        print(f"   Supported: {extractor.SUPPORTED_EXTENSIONS}")
        print(f"   Test file: {file_path.name}")
        print()
        
        if not file_path.exists():
            print(f"   ⚠️  File not found: {file_path}")
            print(f"   💡 Create a sample {test_name.lower()} file to test")
            results[test_name] = "SKIPPED"
            print()
            continue
        
        # Run extraction
        result = extractor.extract_safe(file_path)
        
        if result.success:
            print("   ✅ Extraction successful!")
            print()
            print("   📋 METADATA:")
            for key, value in list(result.metadata.items())[:6]:  # First 6 items
                print(f"      {key}: {value}")
            if len(result.metadata) > 6:
                print(f"      ... and {len(result.metadata) - 6} more")
            print()
            
            print("   📦 STRUCTURED DATA:")
            for key, value in result.structured_data.items():
                if key not in ["tables", "records"]:  # Skip large data
                    print(f"      {key}: {value}")
            print()
            
            # Show text preview
            text_preview = result.raw_text[:300].replace('\n', ' ')
            print(f"   📝 TEXT PREVIEW (first 300 chars):")
            print(f"      {text_preview}...")
            print(f"      Total: {len(result.raw_text)} characters")
            
            results[test_name] = "PASSED"
        else:
            print(f"   ❌ Extraction failed: {result.error}")
            results[test_name] = "FAILED"
        
        print()
        print()
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for test_name, status in results.items():
        icon = "✅" if status == "PASSED" else "⚠️" if status == "SKIPPED" else "❌"
        print(f"{icon} {test_name}: {status}")
    print()
    
    passed = sum(1 for s in results.values() if s == "PASSED")
    total = len([s for s in results.values() if s != "SKIPPED"])
    skipped = sum(1 for s in results.values() if s == "SKIPPED")
    
    print(f"Results: {passed}/{total} passed", end="")
    if skipped > 0:
        print(f" ({skipped} skipped)")
    else:
        print()
    print()
    
    # Next steps
    if skipped > 0:
        print("📝 TO TEST SKIPPED EXTRACTORS:")
        print("   1. Create sample files in the backend folder:")
        if "Image (OCR)" in results and results["Image (OCR)"] == "SKIPPED":
            print("      - sample_receipt.jpg or .png (image of a receipt)")
            print("      - Install Tesseract: See TESSERACT_SETUP_GUIDE.md")
        if "Excel/CSV" in results and results["Excel/CSV"] == "SKIPPED":
            print("      - sample_expenses.xlsx or .csv (expense spreadsheet)")
        print("   2. Run this test again")
        print()
    
    if passed == total and total > 0:
        print("🎉 All extractors working perfectly!")
        print("✅ Ready to proceed with DocumentProcessor orchestrator")
    
    print("=" * 70)


if __name__ == "__main__":
    test_all_extractors()
