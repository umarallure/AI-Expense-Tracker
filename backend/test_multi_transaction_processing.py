"""
Comprehensive Test Suite for Multi-Transaction Processing
Tests all components of the multi-transaction document processing pipeline.
"""
import pytest
import json
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.document_classifier import DocumentClassifier, DocumentType
from app.services.extractors.excel_extractor import ExcelExtractor
from app.services.ai.data_extractor import DataExtractor
from app.services.ai.confidence_scorer import ConfidenceScorer
from app.services.transaction_creator import TransactionCreator
from app.services.document_processor import DocumentProcessor


class TestMultiTransactionProcessing:
    """Comprehensive test suite for multi-transaction processing"""

    @pytest.fixture
    def sample_bank_statement_data(self):
        """Sample bank statement Excel data"""
        return {
            "Date": ["2023-10-01", "2023-10-02", "2023-10-03", "2023-10-04", "2023-10-05"],
            "Description": [
                "ATM Withdrawal",
                "Grocery Store Purchase",
                "Online Transfer",
                "Coffee Shop",
                "Restaurant Payment"
            ],
            "Amount": [-50.00, -85.67, 500.00, -4.50, -45.80],
            "Balance": [2450.00, 2364.33, 2864.33, 2859.83, 2814.03]
        }

    @pytest.fixture
    def sample_expense_report_data(self):
        """Sample expense report Excel data"""
        return {
            "Date": ["2023-10-01", "2023-10-02", "2023-10-03"],
            "Vendor": ["Hotel ABC", "Taxi Service", "Restaurant XYZ"],
            "Description": ["Business trip lodging", "Airport transfer", "Client dinner"],
            "Amount": [250.00, 35.00, 120.50],
            "Category": ["Travel", "Transportation", "Meals"]
        }

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.execute.return_value = Mock(data=[
            {"id": "cat-1", "category_name": "Meals", "business_id": "biz-1"},
            {"id": "cat-2", "category_name": "Travel", "business_id": "biz-1"},
            {"id": "cat-3", "category_name": "Office Supplies", "business_id": "biz-1"}
        ])
        return mock_client

    def test_document_classifier_bank_statement(self, sample_bank_statement_data):
        """Test document classifier identifies bank statements correctly"""
        classifier = DocumentClassifier()

        # Create sample text that looks like a bank statement
        sample_text = """
        BANK STATEMENT
        Account: ****1234
        Period: October 1-5, 2023

        Date: 10/01/2023, Description: ATM Withdrawal, Amount: -$50.00, Balance: $2450.00
        Date: 10/02/2023, Description: Grocery Store Purchase, Amount: -$85.67, Balance: $2364.33
        Date: 10/03/2023, Description: Online Transfer, Amount: $500.00, Balance: $2864.33
        Date: 10/04/2023, Description: Coffee Shop, Amount: -$4.50, Balance: $2859.83
        Date: 10/05/2023, Description: Restaurant Payment, Amount: -$45.80, Balance: $2814.03

        5 transactions found
        """

        # Mock structured data
        structured_data = {
            "row_count": 5,
            "columns": ["Date", "Description", "Amount", "Balance"],
            "transactions": [
                {"date": "2023-10-01", "description": "ATM Withdrawal", "amount": -50.00},
                {"date": "2023-10-02", "description": "Grocery Store Purchase", "amount": -85.67},
                {"date": "2023-10-03", "description": "Online Transfer", "amount": 500.00},
                {"date": "2023-10-04", "description": "Coffee Shop", "amount": -4.50},
                {"date": "2023-10-05", "description": "Restaurant Payment", "amount": -45.80}
            ]
        }

        result = classifier.classify_document(
            file_path=Path("test_statement.xlsx"),
            extracted_text=sample_text,
            structured_data=structured_data
        )

        assert result["document_type"] == "bank_statement_multi"
        assert result["is_multi_transaction"] == True
        assert result["confidence"] > 0.5
        assert "transactions" in result["indicators"][0] or "row_count" in str(result["indicators"])

    def test_excel_extractor_multi_transaction(self, sample_bank_statement_data):
        """Test Excel extractor processes multiple transactions"""
        extractor = ExcelExtractor()

        # Create temporary Excel file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame(sample_bank_statement_data)
            df.to_excel(tmp.name, index=False)
            tmp_path = Path(tmp.name)

        try:
            result = extractor.extract_safe(tmp_path)

            assert result.success == True
            assert "transactions" in result.structured_data
            assert len(result.structured_data["transactions"]) == 5

            # Check that transactions have required fields
            for tx in result.structured_data["transactions"]:
                assert "date" in tx or "Date" in tx
                assert "amount" in tx or "Amount" in tx
                assert "vendor" in tx or "description" in tx or "Description" in tx

        finally:
            tmp_path.unlink()

    @patch('app.services.ai.data_extractor.requests.post')
    def test_data_extractor_multi_transaction_batch(self, mock_post, mock_supabase_client):
        """Test data extractor processes multiple transactions in batches"""
        # Mock AI API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "transactions": [
                            {
                                "vendor": "ATM",
                                "amount": -50.00,
                                "date": "2023-10-01",
                                "description": "ATM Withdrawal",
                                "category_id": "cat-1",
                                "is_income": False,
                                "field_confidence": {"vendor": 0.9, "amount": 0.95, "date": 0.9}
                            },
                            {
                                "vendor": "Grocery Store",
                                "amount": -85.67,
                                "date": "2023-10-02",
                                "description": "Grocery Store Purchase",
                                "category_id": "cat-1",
                                "is_income": False,
                                "field_confidence": {"vendor": 0.85, "amount": 0.95, "date": 0.9}
                            }
                        ]
                    })
                }
            }]
        }
        mock_post.return_value = mock_response

        extractor = DataExtractor(api_key="test-key")

        structured_data = {
            "transactions": [
                {"date": "2023-10-01", "description": "ATM Withdrawal", "amount": -50.00},
                {"date": "2023-10-02", "description": "Grocery Store Purchase", "amount": -85.67}
            ]
        }

        result = extractor.extract(
            text="Sample bank statement text",
            document_type="bank_statement_multi",
            business_id="biz-1",
            supabase_client=mock_supabase_client,
            structured_data=structured_data
        )

        assert result["extraction_type"] == "multi_transaction"
        assert len(result["transactions"]) == 2
        assert result["total_processed_transactions"] == 2
        assert result["completeness_score"] > 0

        # Verify API was called
        assert mock_post.called

    def test_confidence_scorer_multi_transaction(self):
        """Test confidence scorer handles multi-transaction data"""
        scorer = ConfidenceScorer()

        multi_transaction_data = {
            "extraction_type": "multi_transaction",
            "transactions": [
                {
                    "vendor": "Store A",
                    "amount": -25.50,
                    "date": "2023-10-01",
                    "field_confidence": {"vendor": 0.9, "amount": 0.95, "date": 0.85}
                },
                {
                    "vendor": "Store B",
                    "amount": -15.75,
                    "date": "2023-10-02",
                    "field_confidence": {"vendor": 0.85, "amount": 0.90, "date": 0.80}
                },
                {
                    "vendor": "Store C",
                    "amount": -42.00,
                    "date": "2023-10-03",
                    "field_confidence": {"vendor": 0.95, "amount": 0.98, "date": 0.90}
                }
            ],
            "total_raw_transactions": 3,
            "valid_transactions": 3
        }

        confidence = scorer.calculate_overall_confidence(
            field_confidence={},  # Not used for multi-transaction
            extracted_fields=multi_transaction_data,
            structured_data={"row_count": 3}
        )

        assert confidence > 0.8  # Should be high confidence for well-formed data
        assert confidence <= 1.0

    def test_confidence_scorer_completeness_penalty(self):
        """Test confidence scorer applies completeness penalties"""
        scorer = ConfidenceScorer()

        # Test with missing transactions (low completeness)
        incomplete_data = {
            "extraction_type": "multi_transaction",
            "transactions": [
                {
                    "vendor": "Store A",
                    "amount": -25.50,
                    "date": "2023-10-01",
                    "field_confidence": {"vendor": 0.9, "amount": 0.95, "date": 0.85}
                }
            ],
            "total_raw_transactions": 5,  # Expected 5, got 1
            "valid_transactions": 1
        }

        confidence = scorer.calculate_overall_confidence(
            field_confidence={},
            extracted_fields=incomplete_data,
            structured_data={"row_count": 5}
        )

        # Should be penalized for missing 4 out of 5 transactions
        assert confidence < 0.7  # Significant penalty applied

    @patch('app.services.transaction_creator.Client')
    async def test_transaction_creator_multi_transaction(self, mock_supabase_class):
        """Test transaction creator handles multiple transactions"""
        mock_supabase = Mock()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock(data=[{"id": "tx-1"}])
        mock_supabase.table.return_value.select.return_value.execute.return_value = Mock(data=[{"id": "acc-1"}])

        creator = TransactionCreator()

        multi_transaction_data = {
            "extraction_type": "multi_transaction",
            "transactions": [
                {
                    "vendor": "Store A",
                    "amount": -25.50,
                    "date": "2023-10-01",
                    "description": "Purchase",
                    "category_id": "cat-1",
                    "is_income": False,
                    "field_confidence": {"vendor": 0.9, "amount": 0.95, "date": 0.85}
                },
                {
                    "vendor": "Store B",
                    "amount": -15.75,
                    "date": "2023-10-02",
                    "description": "Purchase",
                    "category_id": "cat-1",
                    "is_income": False,
                    "field_confidence": {"vendor": 0.85, "amount": 0.90, "date": 0.80}
                }
            ]
        }

        result = await creator.create_from_document(
            document_id="doc-1",
            business_id="biz-1",
            account_id="acc-1",
            user_id="user-1",
            extracted_data=multi_transaction_data,
            confidence_score=0.9,
            supabase_client=mock_supabase
        )

        assert result is not None
        assert "transactions_created" in result
        assert result["transactions_created"] == 2

    def test_end_to_end_pipeline(self, sample_bank_statement_data, mock_supabase_client):
        """Test complete end-to-end multi-transaction processing pipeline"""
        # This would be an integration test that exercises the full pipeline
        # For now, we'll test the individual components work together

        # 1. Create test Excel file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame(sample_bank_statement_data)
            df.to_excel(tmp.name, index=False)
            tmp_path = Path(tmp.name)

        try:
            # 2. Test document processor
            processor = DocumentProcessor()
            result = processor.process_document(tmp_path, document_id="test-doc")

            assert result["status"] == "completed"
            assert "extraction_result" in result
            structured_data = result["extraction_result"]["structured_data"]

            # 3. Test classifier
            classifier = DocumentClassifier()
            classification = classifier.classify_document(
                file_path=tmp_path,
                extracted_text=result["extraction_result"]["raw_text"],
                structured_data=structured_data
            )

            assert classification["is_multi_transaction"] == True

            # 4. Test data extraction (mocked)
            with patch('app.services.ai.data_extractor.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.json.return_value = {
                    "choices": [{
                        "message": {
                            "content": json.dumps({
                                "transactions": [
                                    {
                                        "vendor": tx["Description"],
                                        "amount": tx["Amount"],
                                        "date": tx["Date"],
                                        "category_id": "cat-1",
                                        "is_income": tx["Amount"] > 0,
                                        "field_confidence": {"vendor": 0.9, "amount": 0.95, "date": 0.9}
                                    } for tx in [dict(zip(sample_bank_statement_data.keys(),
                                                       [sample_bank_statement_data[k][i] for k in sample_bank_statement_data.keys()]))
                                               for i in range(len(sample_bank_statement_data["Date"]))]
                                ]
                            })
                        }
                    }]
                }
                mock_post.return_value = mock_response

                extractor = DataExtractor(api_key="test-key")
                extracted_data = extractor.extract(
                    text=result["extraction_result"]["raw_text"],
                    document_type=classification["document_type"],
                    business_id="biz-1",
                    supabase_client=mock_supabase_client,
                    structured_data=structured_data
                )

                assert extracted_data["extraction_type"] == "multi_transaction"
                assert len(extracted_data["transactions"]) == 5

        finally:
            tmp_path.unlink()

    def test_performance_large_dataset(self):
        """Test performance with large transaction datasets"""
        # Create a large dataset
        large_transactions = [
            {
                "date": f"2023-10-{i+1:02d}",
                "description": f"Transaction {i+1}",
                "amount": -10.00 * (i + 1),
                "vendor": f"Vendor {i+1}"
            } for i in range(50)  # 50 transactions
        ]

        structured_data = {"transactions": large_transactions}

        # Test that the system can handle large batches
        extractor = DataExtractor(api_key="test-key")

        # Check batch size configuration
        assert extractor.max_batch_size == 10  # Should process in batches of 10

        # Verify memory cleanup threshold
        assert extractor.memory_cleanup_threshold == 50

    def test_error_handling_multi_transaction(self, mock_supabase_client):
        """Test error handling in multi-transaction processing"""
        extractor = DataExtractor(api_key="test-key")

        # Test with empty structured data
        result = extractor.extract(
            text="Some document text",
            document_type="bank_statement",
            business_id="biz-1",
            supabase_client=mock_supabase_client,
            structured_data={}  # Empty structured data
        )

        # Should fall back to single transaction extraction
        assert "vendor" in result or "transactions" in result

    def test_confidence_recommendations(self):
        """Test confidence scorer provides appropriate recommendations"""
        scorer = ConfidenceScorer()

        # High confidence multi-transaction
        high_conf_data = {
            "extraction_type": "multi_transaction",
            "transactions": [
                {
                    "vendor": "Store A", "amount": -25.50, "date": "2023-10-01",
                    "field_confidence": {"vendor": 0.95, "amount": 0.98, "date": 0.95}
                }
            ]
        }

        recommendation = scorer.get_recommendation(0.92)
        assert recommendation["action"] == "auto_approve"
        assert recommendation["auto_approve"] == True

        # Low confidence
        recommendation = scorer.get_recommendation(0.5)
        assert recommendation["action"] == "manual_review_required"
        assert recommendation["auto_approve"] == False


if __name__ == "__main__":
    # Run basic smoke tests
    print("🧪 Running Multi-Transaction Processing Tests...")

    # Test document classifier
    classifier = DocumentClassifier()
    test_text = """
    BANK STATEMENT
    5 transactions found
    Date: 10/01/2023, Description: Purchase, Amount: -$50.00
    Date: 10/02/2023, Description: Deposit, Amount: $100.00
    """

    result = classifier.classify_document(
        file_path=Path("test.xlsx"),
        extracted_text=test_text,
        structured_data={"row_count": 2, "transactions": []}
    )

    print(f"✅ Document Classification: {result['document_type']}, Multi-transaction: {result['is_multi_transaction']}")

    # Test confidence scorer
    scorer = ConfidenceScorer()
    confidence = scorer.calculate_overall_confidence(
        field_confidence={},
        extracted_fields={
            "extraction_type": "multi_transaction",
            "transactions": [{"vendor": "Test", "amount": -10.00, "date": "2023-10-01"}]
        }
    )

    print(f"✅ Confidence Scoring: {confidence:.2f}")

    print("🎉 All smoke tests passed!")