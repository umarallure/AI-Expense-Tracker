"""
Test script for DocumentProcessor orchestrator
Tests the main document processing pipeline.
"""
import sys
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.document_processor import DocumentProcessor


def test_document_processor():
    """Test DocumentProcessor orchestrator"""
    print("=" * 70)
    print("DOCUMENT PROCESSOR ORCHESTRATOR TEST")
    print("=" * 70)
    print()
    
    # Initialize processor
    processor = DocumentProcessor()
    print("✅ DocumentProcessor initialized")
    print()
    
    # Show supported file types
    print("📋 SUPPORTED FILE TYPES:")
    for info in processor.get_extractor_info():
        print(f"   {info['name']}:")
        print(f"      Extensions: {', '.join(info['supported_extensions'])}")
    print()
    
    print(f"📁 All supported extensions: {', '.join(processor.get_supported_extensions())}")
    print()
    print("-" * 70)
    print()
    
    # Test with sample files
    test_files = [
        "sample_invoice.pdf",
        "sample_receipt.jpg",
        "sample_expenses.xlsx",
        "sample_expenses.csv"
    ]
    
    print("🧪 TESTING DOCUMENT PROCESSING:")
    print()
    
    for file_name in test_files:
        file_path = Path(file_name)
        print(f"📄 File: {file_name}")
        print(f"   Extension: {file_path.suffix}")
        
        # Check if file exists
        if not file_path.exists():
            print(f"   ⚠️  File not found (skipped)")
            print()
            continue
        
        # Validate file type
        is_supported, error = processor.validate_file_type(file_path)
        if not is_supported:
            print(f"   ❌ {error}")
            print()
            continue
        
        # Get extractor
        extractor = processor.get_extractor_for_file(file_path)
        print(f"   📦 Extractor: {extractor.name}")
        
        # Process document
        print(f"   ⏳ Processing...")
        result = processor.process_document(file_path)
        
        # Show results
        if result["status"] == "completed":
            print(f"   ✅ Status: {result['status']}")
            print(f"   ⏱️  Time: {result['processing_time_ms']}ms")
            
            if result["extraction_result"]:
                ext_result = result["extraction_result"]
                print(f"   📝 Extracted: {ext_result['text_length']} chars, {ext_result['word_count']} words")
                
                # Show text preview
                text_preview = ext_result['raw_text'][:200].replace('\n', ' ')
                print(f"   💬 Preview: {text_preview}...")
        else:
            print(f"   ❌ Status: {result['status']}")
            print(f"   ⚠️  Error: {result['error']}")
        
        print()
    
    print("-" * 70)
    print()
    
    # Full processing result example
    test_file = Path("sample_invoice.pdf")
    if test_file.exists():
        print("📊 DETAILED PROCESSING RESULT (sample_invoice.pdf):")
        print()
        result = processor.process_document(test_file)
        
        # Pretty print result (excluding large text)
        result_copy = result.copy()
        if result_copy.get("extraction_result"):
            result_copy["extraction_result"]["raw_text"] = result_copy["extraction_result"]["raw_text"][:100] + "..."
            if "tables" in result_copy["extraction_result"].get("structured_data", {}):
                result_copy["extraction_result"]["structured_data"]["tables"] = "[TABLE DATA OMITTED]"
            if "records" in result_copy["extraction_result"].get("structured_data", {}):
                result_copy["extraction_result"]["structured_data"]["records"] = "[RECORDS OMITTED]"
        
        print(json.dumps(result_copy, indent=2))
        print()
    
    print("=" * 70)
    print("✅ DocumentProcessor orchestrator test complete!")
    print("🎯 Next: Add database columns and API endpoints")
    print("=" * 70)


if __name__ == "__main__":
    test_document_processor()
