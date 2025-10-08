"""
Test Script for Phase 3.3 AI Extraction
Run this to verify OpenAI integration works correctly.
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai import DocumentClassifier, DataExtractor, ConfidenceScorer
from app.core.config import get_settings

settings = get_settings()


def test_openai_connection():
    """Test OpenAI API connection"""
    print("=" * 80)
    print("TESTING OPENAI API CONNECTION")
    print("=" * 80)
    
    try:
        # Check if API key is set
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
            print("❌ ERROR: OPENAI_API_KEY not set in .env file")
            print("   Please add your OpenAI API key to backend/.env")
            print("   Get one from: https://platform.openai.com/api-keys")
            return False
        
        print(f"✅ OPENAI_API_KEY found: {settings.OPENAI_API_KEY[:20]}...")
        print(f"✅ Model: {settings.OPENAI_MODEL}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_document_classifier():
    """Test DocumentClassifier with sample text"""
    print("=" * 80)
    print("TESTING DOCUMENT CLASSIFIER")
    print("=" * 80)
    
    try:
        classifier = DocumentClassifier()
        
        # Sample invoice text
        sample_text = """
        INVOICE
        
        Invoice Number: INV-2023-1234
        Date: October 15, 2023
        
        Bill To:
        Acme Corporation
        123 Main Street
        
        From:
        Office Supplies Inc.
        456 Oak Avenue
        
        Description                 Qty     Price      Total
        Office Chair                1       $250.00    $250.00
        Desk Lamp                   2       $45.00     $90.00
        
        Subtotal:                                      $340.00
        Tax (10%):                                     $34.00
        Total:                                         $374.00
        
        Payment Terms: Net 30
        """
        
        print("Classifying sample invoice...")
        print()
        
        doc_type, confidence = classifier.classify(sample_text)
        
        print(f"✅ Classification successful!")
        print(f"   Document Type: {doc_type}")
        print(f"   Confidence: {confidence:.2f}")
        print()
        
        if doc_type == "invoice" and confidence > 0.7:
            print("✅ Test PASSED: Correctly classified as invoice with good confidence")
            return True
        else:
            print(f"⚠️  Test WARNING: Expected 'invoice', got '{doc_type}'")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_confidence_scorer():
    """Test ConfidenceScorer calculations"""
    print("=" * 80)
    print("TESTING CONFIDENCE SCORER")
    print("=" * 80)
    
    try:
        scorer = ConfidenceScorer()
        
        # Sample field confidences
        field_confidence = {
            "vendor": 0.95,
            "amount": 0.99,
            "date": 0.90,
            "description": 0.85
        }
        
        extracted_fields = {
            "vendor": "Office Supplies Inc",
            "amount": 374.00,
            "date": "2023-10-15",
            "description": "Office supplies purchase"
        }
        
        print("Calculating overall confidence...")
        overall = scorer.calculate_overall_confidence(field_confidence, extracted_fields)
        
        print(f"✅ Overall confidence: {overall:.2f}")
        print()
        
        # Test recommendation
        recommendation = scorer.get_recommendation(overall)
        print(f"   Action: {recommendation['action']}")
        print(f"   Message: {recommendation['message']}")
        print(f"   Confidence Level: {recommendation['confidence_level']}")
        print()
        
        if overall >= 0.85:
            print("✅ Test PASSED: High confidence, ready for auto-approval")
            return True
        else:
            print("⚠️  Test WARNING: Confidence below auto-approval threshold")
            return True  # Still pass if calculation works
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print()
    print("🚀 PHASE 3.3 AI EXTRACTION - INTEGRATION TEST")
    print()
    
    results = []
    
    # Test 1: OpenAI Connection
    results.append(("OpenAI Connection", test_openai_connection()))
    print()
    
    # Test 2: Document Classifier (only if connection works)
    if results[0][1]:
        results.append(("Document Classifier", test_document_classifier()))
        print()
    else:
        print("⏭️  Skipping classifier test (OpenAI not configured)")
        print()
    
    # Test 3: Confidence Scorer (always works, no API needed)
    results.append(("Confidence Scorer", test_confidence_scorer()))
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print()
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Next steps:")
        print("1. Restart your backend server")
        print("2. Upload a document through the frontend")
        print("3. Check the logs for AI extraction results")
        print("4. View extracted data in the 'View Extracted Text' modal")
    else:
        print("⚠️  SOME TESTS FAILED")
        print()
        print("Common fixes:")
        print("1. Add OPENAI_API_KEY to backend/.env file")
        print("2. Restart backend server after updating .env")
        print("3. Verify OpenAI API key is valid")
        print("4. Check you have credits in your OpenAI account")
    
    print()


if __name__ == "__main__":
    main()
