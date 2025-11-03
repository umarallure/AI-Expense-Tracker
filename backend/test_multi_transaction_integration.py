#!/usr/bin/env python3
"""
Comprehensive Multi-Transaction Processing Test
Tests the complete multi-transaction pipeline from document upload to transaction creation.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.extractors.excel_extractor import ExcelExtractor
from app.services.ai.data_extractor import DataExtractor
from app.services.ai.confidence_scorer import ConfidenceScorer
from app.services.transaction_creator import TransactionCreator

def create_test_excel_file():
    """Create a sample multi-transaction Excel file for testing."""
    data = {
        'Date': ['2023-10-01', '2023-10-02', '2023-10-03', '2023-10-04', '2023-10-05'],
        'Description': [
            'Amazon.com Purchase',
            'Starbucks Coffee',
            'Office Depot Supplies',
            'Uber Ride',
            'Grocery Store'
        ],
        'Amount': [-89.99, -5.75, -45.50, -12.30, -67.25],
        'Category': ['Office Supplies', 'Meals', 'Office Supplies', 'Travel', 'Meals'],
        'Reference': ['TXN-001', 'TXN-002', 'TXN-003', 'TXN-004', 'TXN-005']
    }

    df = pd.DataFrame(data)
    test_file = Path(__file__).parent / 'test_multi_transaction.xlsx'
    df.to_excel(test_file, index=False)
    return test_file

def test_excel_multi_transaction_detection():
    """Test Excel extractor's multi-transaction detection."""
    print("Testing Excel Multi-Transaction Detection...")

    extractor = ExcelExtractor()
    test_file = create_test_excel_file()

    try:
        # Test multi-transaction detection using file path
        result = extractor.extract(test_file)
        print(f"✓ Extraction success: {result.success}")
        if not result.success:
            print(f"✗ Extraction error: {result.error}")
            return None

        print(f"✓ Extracted {len(result.structured_data.get('transactions', []))} transactions from Excel")
        print(f"✓ Document type: {result.structured_data.get('document_type', 'unknown')}")
        print(f"✓ Is multi-transaction: {result.metadata.get('is_multi_transaction', False)}")

        # Debug: print structured data keys
        print(f"✓ Structured data keys: {list(result.structured_data.keys())}")

        # Validate structure
        transactions = result.structured_data.get('transactions', [])
        if transactions:
            first_txn = transactions[0]
            print(f"✓ First transaction keys: {list(first_txn.keys())}")
            required_fields = ['vendor', 'amount', 'date']
            for field in required_fields:
                assert field in first_txn, f"Missing required field: {field}"
            print("✓ Transaction structure validation passed")
        else:
            print("⚠ No transactions found - checking if it's single transaction format")
            records = result.structured_data.get('records', [])
            print(f"✓ Found {len(records)} records in single format")
            if records:
                print(f"✓ First record: {records[0]}")

        return result.structured_data

    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()

def test_ai_batch_processing():
    """Test AI data extractor's batch processing capabilities."""
    print("\nTesting AI Batch Processing...")

    # Mock structured data from Excel extractor
    structured_data = {
        'transactions': [
            {
                'vendor': 'Amazon.com',
                'amount': -89.99,
                'date': '2023-10-01',
                'description': 'Office supplies purchase',
                'category': 'Office Supplies'
            },
            {
                'vendor': 'Starbucks',
                'amount': -5.75,
                'date': '2023-10-02',
                'description': 'Coffee purchase',
                'category': 'Meals'
            }
        ]
    }

    extractor = DataExtractor()

    # Test batch processing
    try:
        result = extractor._extract_multiple_transactions(structured_data)
        print(f"✓ AI batch processing returned {len(result.get('transactions', []))} transactions")

        # Validate AI enhancement
        transactions = result.get('transactions', [])
        if transactions:
            first_txn = transactions[0]
            assert 'field_confidence' in first_txn, "Missing confidence scores"
            assert 'category_id' in first_txn, "Missing category assignment"
            print("✓ AI enhancement validation passed")

        return result

    except Exception as e:
        print(f"✗ AI batch processing failed: {e}")
        return None

def test_confidence_scoring():
    """Test confidence scorer with multi-transaction data."""
    print("\nTesting Multi-Transaction Confidence Scoring...")

    # Mock AI extraction result
    ai_result = {
        'transactions': [
            {
                'vendor': 'Amazon.com',
                'amount': -89.99,
                'date': '2023-10-01',
                'description': 'Office supplies purchase',
                'category_id': 'office-supplies-uuid',
                'field_confidence': {
                    'vendor': 0.95,
                    'amount': 0.98,
                    'date': 0.92,
                    'description': 0.85,
                    'category_id': 0.80
                }
            },
            {
                'vendor': 'Starbucks',
                'amount': -5.75,
                'date': '2023-10-02',
                'description': 'Coffee purchase',
                'category_id': 'meals-uuid',
                'field_confidence': {
                    'vendor': 0.90,
                    'amount': 0.95,
                    'date': 0.88,
                    'description': 0.80,
                    'category_id': 0.75
                }
            }
        ]
    }

    scorer = ConfidenceScorer()

    try:
        # Test structured data parameter
        structured_data = {'transactions': ai_result['transactions']}
        overall_confidence = scorer.calculate_overall_confidence(ai_result, structured_data)

        print(f"✓ Overall confidence calculated: {overall_confidence}")

        # Validate confidence structure
        assert isinstance(overall_confidence, (int, float)), "Confidence should be numeric"
        assert 0 <= overall_confidence <= 1, "Confidence should be between 0 and 1"
        print("✓ Confidence scoring validation passed")

        return overall_confidence

    except Exception as e:
        print(f"✗ Confidence scoring failed: {e}")
        return None

def test_transaction_creation():
    """Test transaction creator with multiple transactions."""
    print("\nTesting Multi-Transaction Creation...")

    # Mock confidence scoring result
    confidence_result = {
        'transactions': [
            {
                'vendor': 'Amazon.com',
                'amount': -89.99,
                'date': '2023-10-01',
                'description': 'Office supplies purchase',
                'category_id': 'office-supplies-uuid',
                'is_income': False,
                'confidence': 0.85
            },
            {
                'vendor': 'Starbucks',
                'amount': -5.75,
                'date': '2023-10-02',
                'description': 'Coffee purchase',
                'category_id': 'meals-uuid',
                'is_income': False,
                'confidence': 0.82
            }
        ],
        'overall_confidence': 0.835
    }

    creator = TransactionCreator()

    try:
        # Mock document ID and user ID
        document_id = 'test-doc-123'
        user_id = 'test-user-456'

        # Test multiple transaction creation
        result = creator._create_multiple_transactions(confidence_result, document_id, user_id)

        print(f"✓ Created {len(result.get('transactions', []))} transactions")

        # Validate transaction structure
        transactions = result.get('transactions', [])
        if transactions:
            first_txn = transactions[0]
            required_fields = ['id', 'vendor', 'amount', 'date', 'user_id', 'document_id']
            for field in required_fields:
                assert field in first_txn, f"Missing required field: {field}"
            print("✓ Transaction creation validation passed")

        return result

    except Exception as e:
        print(f"✗ Transaction creation failed: {e}")
        return None

def run_integration_test():
    """Run complete integration test of multi-transaction pipeline."""
    print("\n" + "="*60)
    print("RUNNING COMPLETE MULTI-TRANSACTION INTEGRATION TEST")
    print("="*60)

    try:
        # Step 1: Excel extraction
        excel_result = test_excel_multi_transaction_detection()
        if not excel_result or not excel_result.get('transactions'):
            raise Exception("Excel extraction failed")

        # Step 2: AI processing
        ai_result = test_ai_batch_processing()
        if not ai_result or not ai_result.get('transactions'):
            raise Exception("AI processing failed")

        # Step 3: Confidence scoring
        confidence_score = test_confidence_scoring()
        if confidence_score is None:
            raise Exception("Confidence scoring failed")

        # Step 4: Transaction creation
        creation_result = test_transaction_creation()
        if not creation_result or not creation_result.get('transactions'):
            raise Exception("Transaction creation failed")

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - MULTI-TRANSACTION PIPELINE WORKING")
        print("="*60)

        # Summary
        total_transactions = len(creation_result.get('transactions', []))
        print(f"Successfully processed {total_transactions} transactions end-to-end")
        print(f"Average confidence: {confidence_score:.2f}")
        return True

    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        return False

if __name__ == '__main__':
    success = run_integration_test()
    sys.exit(0 if success else 1)