#!/usr/bin/env python3
"""
Test script for processing multi-transaction PDF document
"""
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_processor import DocumentProcessor
from app.services.document_classifier import DocumentClassifier
from app.services.ai.data_extractor import DataExtractor
from app.services.ai.confidence_scorer import ConfidenceScorer
from app.core.config import get_settings
from app.db.supabase import get_supabase_client

def test_pdf_processing(pdf_path: str):
    """
    Test processing of a multi-transaction PDF document
    
    Args:
        pdf_path: Path to the PDF file
    """
    print("=" * 80)
    print("🧪 TESTING MULTI-TRANSACTION PDF PROCESSING")
    print("=" * 80)
    
    pdf_file = Path(pdf_path)
    
    if not pdf_file.exists():
        print(f"❌ ERROR: File not found: {pdf_path}")
        return
    
    print(f"\n📄 Processing file: {pdf_file.name}")
    print(f"   Size: {pdf_file.stat().st_size / 1024:.2f} KB")
    
    try:
        # Step 1: Document Processor - Extract text
        print("\n" + "=" * 80)
        print("STEP 1: EXTRACTING TEXT FROM PDF")
        print("=" * 80)
        
        processor = DocumentProcessor()
        result = processor.process_document(pdf_file, document_id="test-doc-001")
        
        if result["status"] != "completed":
            print(f"❌ Text extraction failed: {result.get('error')}")
            return
        
        extraction_result = result["extraction_result"]
        raw_text = extraction_result["raw_text"]
        structured_data = extraction_result.get("structured_data", {})
        
        print(f"✅ Text extraction successful!")
        print(f"   - Raw text length: {len(raw_text)} characters")
        print(f"   - Word count: {extraction_result['word_count']}")
        print(f"   - Extractor used: {result['extractor_used']}")
        print(f"   - Processing time: {result['processing_time_ms']}ms")
        
        # Show text preview
        print(f"\n📝 Text Preview (first 500 chars):")
        print("-" * 80)
        print(raw_text[:500])
        print("-" * 80)
        
        # Step 2: Document Classifier - Classify document type
        print("\n" + "=" * 80)
        print("STEP 2: CLASSIFYING DOCUMENT TYPE")
        print("=" * 80)
        
        classifier = DocumentClassifier()
        classification = classifier.classify_document(
            file_path=pdf_file,
            extracted_text=raw_text,
            structured_data=structured_data
        )
        
        print(f"✅ Document classification complete!")
        print(f"   - Document type: {classification['document_type']}")
        print(f"   - Is multi-transaction: {classification['is_multi_transaction']}")
        print(f"   - Classification confidence: {classification['confidence']:.2f}")
        print(f"   - Multi-transaction confidence: {classification['multi_transaction_confidence']:.2f}")
        print(f"   - Detection method: {classification['detection_method']}")
        
        if classification['indicators']:
            print(f"   - Indicators found: {len(classification['indicators'])}")
            for indicator in classification['indicators'][:3]:
                print(f"     • {indicator}")
        
        # Step 3: AI Data Extraction
        print("\n" + "=" * 80)
        print("STEP 3: EXTRACTING STRUCTURED DATA WITH AI")
        print("=" * 80)
        
        settings = get_settings()
        supabase = get_supabase_client()
        
        # Use a proper UUID for test business ID
        import uuid
        test_business_id = str(uuid.uuid4())
        
        print(f"   - Using AI model: openai/gpt-4o-mini")
        print(f"   - Document type: {classification['document_type']}")
        print(f"   - Multi-transaction mode: {classification['is_multi_transaction']}")
        print(f"   - Test business ID: {test_business_id}")
        
        extractor = DataExtractor(api_key=settings.OPENAI_API_KEY)
        
        extracted_data = extractor.extract(
            text=raw_text,
            document_type=classification['document_type'],
            business_id=test_business_id,
            supabase_client=supabase,
            structured_data=structured_data
        )
        
        print(f"\n✅ AI extraction complete!")
        
        # Check if multi-transaction result
        if extracted_data.get("extraction_type") == "multi_transaction":
            print(f"   - Extraction type: MULTI-TRANSACTION")
            print(f"   - Total raw transactions: {extracted_data.get('total_raw_transactions', 0)}")
            print(f"   - Total processed transactions: {extracted_data.get('total_processed_transactions', 0)}")
            print(f"   - Valid transactions: {extracted_data.get('valid_transactions', 0)}")
            print(f"   - Completeness score: {extracted_data.get('completeness_score', 0):.2f}")
            
            transactions = extracted_data.get("transactions", [])
            print(f"\n📊 EXTRACTED TRANSACTIONS ({len(transactions)}):")
            print("=" * 80)
            
            for i, tx in enumerate(transactions[:10], 1):  # Show first 10
                print(f"\n{i}. Transaction:")
                print(f"   - Vendor: {tx.get('vendor', 'N/A')}")
                print(f"   - Amount: ${tx.get('amount', 0):.2f}")
                print(f"   - Date: {tx.get('date', 'N/A')}")
                print(f"   - Description: {tx.get('description', 'N/A')[:50]}...")
                
                if tx.get('field_confidence'):
                    avg_conf = sum(tx['field_confidence'].values()) / len(tx['field_confidence'])
                    print(f"   - Avg confidence: {avg_conf:.2f}")
            
            if len(transactions) > 10:
                print(f"\n   ... and {len(transactions) - 10} more transactions")
        
        else:
            print(f"   - Extraction type: SINGLE TRANSACTION")
            print(f"   - Vendor: {extracted_data.get('vendor', 'N/A')}")
            print(f"   - Amount: ${extracted_data.get('amount', 0):.2f}")
            print(f"   - Date: {extracted_data.get('date', 'N/A')}")
            print(f"   - Description: {extracted_data.get('description', 'N/A')}")
        
        # Step 4: Confidence Scoring
        print("\n" + "=" * 80)
        print("STEP 4: CALCULATING CONFIDENCE SCORES")
        print("=" * 80)
        
        scorer = ConfidenceScorer()
        
        field_confidence = extracted_data.get("field_confidence", {})
        overall_confidence = scorer.calculate_overall_confidence(
            field_confidence=field_confidence,
            extracted_fields=extracted_data,
            structured_data=structured_data
        )
        
        recommendation = scorer.get_recommendation(overall_confidence)
        
        print(f"✅ Confidence calculation complete!")
        print(f"   - Overall confidence: {overall_confidence:.2f}")
        print(f"   - Confidence level: {recommendation['confidence_level']}")
        print(f"   - Recommendation: {recommendation['action']}")
        print(f"   - Auto-approve: {recommendation['auto_approve']}")
        print(f"   - Message: {recommendation['message']}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 PROCESSING SUMMARY")
        print("=" * 80)
        
        print(f"✅ Document processed successfully!")
        print(f"   - File: {pdf_file.name}")
        print(f"   - Document type: {classification['document_type']}")
        print(f"   - Multi-transaction: {classification['is_multi_transaction']}")
        
        if extracted_data.get("extraction_type") == "multi_transaction":
            print(f"   - Transactions extracted: {extracted_data.get('valid_transactions', 0)}")
            print(f"   - Completeness: {extracted_data.get('completeness_score', 0):.0%}")
        
        print(f"   - Overall confidence: {overall_confidence:.0%}")
        print(f"   - Recommendation: {recommendation['action']}")
        
        print("\n" + "=" * 80)
        print("🎉 TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR during processing:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        print("\n📋 Full traceback:")
        print(traceback.format_exc())


if __name__ == "__main__":
    # Test with the provided PDF file
    pdf_path = r"C:\Users\Z C\Desktop\AgenticfiAI\multitransaction.pdf"
    
    test_pdf_processing(pdf_path)
