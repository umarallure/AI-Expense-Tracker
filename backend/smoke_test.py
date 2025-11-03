#!/usr/bin/env python3
"""
Simple smoke test for multi-transaction processing components
"""
from pathlib import Path

# Test document classifier
from app.services.document_classifier import DocumentClassifier

print("🧪 Testing Document Classifier...")
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
from app.services.ai.confidence_scorer import ConfidenceScorer

print("🧪 Testing Confidence Scorer...")
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