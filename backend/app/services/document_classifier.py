"""
Document Classifier Service
Classifies documents by type and identifies multi-transaction documents
for appropriate processing routing.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from enum import Enum


class DocumentType(Enum):
    """Document type classifications"""
    RECEIPT = "receipt"
    INVOICE = "invoice"
    BANK_STATEMENT = "bank_statement"
    EXPENSE_REPORT = "expense_report"
    CREDIT_CARD_STATEMENT = "credit_card_statement"
    UTILITY_BILL = "utility_bill"
    TAX_DOCUMENT = "tax_document"
    PAYSTUB = "paystub"
    CONTRACT = "contract"
    OTHER = "other"

    # Multi-transaction variants
    BANK_STATEMENT_MULTI = "bank_statement_multi"
    EXPENSE_REPORT_MULTI = "expense_report_multi"
    CREDIT_CARD_STATEMENT_MULTI = "credit_card_statement_multi"


class DocumentClassifier:
    """
    Classifies documents by type and detects multi-transaction documents.
    Uses content analysis and file characteristics to determine document type
    and processing requirements.
    """

    def __init__(self):
        """Initialize classifier with detection patterns"""
        self.multi_transaction_keywords = {
            DocumentType.BANK_STATEMENT_MULTI: [
                r'\btransactions?\b.*\b\d+\b',  # "transactions" followed by number
                r'\bstatement\b.*\bperiod\b',   # "statement period"
                r'\bbalance\b.*\btransactions?\b', # balance and transactions
                r'\bdeposits?\b.*\bwithdrawals?\b', # deposits and withdrawals
                r'\btransaction\s+history\b',   # transaction history
                r'\bposted\s+transactions?\b',   # posted transactions
                r'\bpending\s+transactions?\b',   # pending transactions
            ],
            DocumentType.EXPENSE_REPORT_MULTI: [
                r'\bexpense\s+report\b',         # expense report
                r'\bmultiple\s+expenses?\b',     # multiple expenses
                r'\bitemized\s+expenses?\b',     # itemized expenses
                r'\bexpense\s+details?\b',       # expense details
                r'\breimbursements?\b.*\bitems?\b', # reimbursements items
            ],
            DocumentType.CREDIT_CARD_STATEMENT_MULTI: [
                r'\bcredit\s+card\s+statement\b', # credit card statement
                r'\bcharges?\b.*\b\d+\b',        # charges followed by number
                r'\bpurchases?\b.*\bcharges?\b', # purchases and charges
                r'\btransaction\s+summary\b',    # transaction summary
            ]
        }

        self.single_transaction_keywords = {
            DocumentType.RECEIPT: [
                r'\breceipt\b',
                r'\bpaid\s+(?:in\s+)?full\b',
                r'\btotal\s+(?:due|amount)\b',
                r'\bchange\s+(?:due|given)\b',
            ],
            DocumentType.INVOICE: [
                r'\binvoice\b',
                r'\bbill\s+to\b',
                r'\bdue\s+date\b',
                r'\bpayment\s+terms\b',
            ],
            DocumentType.UTILITY_BILL: [
                r'\butilities?\b',
                r'\belectric\b',
                r'\bgas\b',
                r'\bwater\b',
                r'\binternet\b',
            ],
            DocumentType.PAYSTUB: [
                r'\bpayroll\b',
                r'\bsalary\b',
                r'\bpay\s+period\b',
                r'\bgross\s+pay\b',
            ]
        }

    def classify_document(
        self,
        file_path: Path,
        extracted_text: str,
        structured_data: Optional[Dict] = None
    ) -> Dict:
        """
        Classify document type and determine if it's multi-transaction

        Args:
            file_path: Path to the document file
            extracted_text: Raw extracted text from document
            structured_data: Optional structured data from extractor

        Returns:
            Classification result with type, confidence, and multi-transaction flag
        """
        result = {
            "document_type": DocumentType.OTHER.value,
            "is_multi_transaction": False,
            "confidence": 0.0,
            "detection_method": "fallback",
            "multi_transaction_confidence": 0.0,
            "indicators": []
        }

        # First, try file-based classification
        file_based_type = self._classify_by_file_characteristics(file_path, structured_data)
        if file_based_type:
            result["document_type"] = file_based_type.value
            result["detection_method"] = "file_characteristics"
            result["confidence"] = 0.8

        # Then, analyze content for more specific classification
        content_classification = self._classify_by_content(extracted_text)
        if content_classification["confidence"] > result["confidence"]:
            result.update(content_classification)
            result["detection_method"] = "content_analysis"

        # Check for multi-transaction indicators
        multi_check = self._check_multi_transaction(extracted_text, structured_data)
        result["is_multi_transaction"] = multi_check["is_multi"]
        result["multi_transaction_confidence"] = multi_check["confidence"]
        result["indicators"] = multi_check["indicators"]

        # Adjust document type for multi-transaction variants
        if result["is_multi_transaction"] and result["multi_transaction_confidence"] > 0.7:
            result["document_type"] = self._get_multi_transaction_variant(result["document_type"])

        return result

    def _classify_by_file_characteristics(
        self,
        file_path: Path,
        structured_data: Optional[Dict]
    ) -> Optional[DocumentType]:
        """
        Classify based on file name and structured data characteristics

        Args:
            file_path: Path to the file
            structured_data: Structured data from extractor

        Returns:
            DocumentType if detectable, None otherwise
        """
        filename = file_path.name.lower()

        # Check filename patterns
        if any(term in filename for term in ['statement', 'stmt']):
            if any(term in filename for term in ['bank', 'checking', 'savings']):
                return DocumentType.BANK_STATEMENT
            elif any(term in filename for term in ['credit', 'card', 'visa', 'mastercard']):
                return DocumentType.CREDIT_CARD_STATEMENT

        if any(term in filename for term in ['invoice', 'bill']):
            return DocumentType.INVOICE

        if any(term in filename for term in ['receipt', 'reciept']):
            return DocumentType.RECEIPT

        if any(term in filename for term in ['expense', 'expenses', 'reimbursement']):
            return DocumentType.EXPENSE_REPORT

        # Check structured data patterns
        if structured_data and isinstance(structured_data, dict):
            # Excel files with transaction-like columns
            if 'columns' in structured_data:
                columns = [col.lower() for col in structured_data['columns']]
                transaction_indicators = ['date', 'amount', 'description', 'vendor', 'transaction']

                if sum(1 for col in columns if any(ind in col for ind in transaction_indicators)) >= 3:
                    # Check if it looks like a bank statement
                    if any(term in ' '.join(columns) for term in ['balance', 'deposit', 'withdrawal']):
                        return DocumentType.BANK_STATEMENT
                    else:
                        return DocumentType.EXPENSE_REPORT

        return None

    def _classify_by_content(self, text: str) -> Dict:
        """
        Classify document based on text content analysis

        Args:
            text: Extracted text content

        Returns:
            Classification result dictionary
        """
        text_lower = text.lower()
        best_match = {
            "document_type": DocumentType.OTHER.value,
            "confidence": 0.0
        }

        # Check single transaction types
        for doc_type, patterns in self.single_transaction_keywords.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text_lower, re.IGNORECASE))
            confidence = min(matches / len(patterns), 1.0)

            if confidence > best_match["confidence"]:
                best_match = {
                    "document_type": doc_type.value,
                    "confidence": confidence
                }

        return best_match

    def _check_multi_transaction(
        self,
        text: str,
        structured_data: Optional[Dict] = None
    ) -> Dict:
        """
        Check if document contains multiple transactions

        Args:
            text: Extracted text content
            structured_data: Optional structured data

        Returns:
            Multi-transaction analysis result
        """
        result = {
            "is_multi": False,
            "confidence": 0.0,
            "indicators": []
        }

        text_lower = text.lower()
        indicators_found = []

        # Check text-based indicators
        for doc_type, patterns in self.multi_transaction_keywords.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    indicators_found.append(f"{doc_type.value}: {pattern}")
                    result["confidence"] = min(result["confidence"] + 0.2, 1.0)

        # Check structured data indicators
        if structured_data and isinstance(structured_data, dict):
            # Excel/CSV with multiple rows
            if 'row_count' in structured_data and structured_data['row_count'] > 5:
                indicators_found.append(f"high_row_count: {structured_data['row_count']} rows")
                result["confidence"] = min(result["confidence"] + 0.3, 1.0)

            # Multiple amount columns or transaction-like data
            if 'columns' in structured_data:
                columns = [col.lower() for col in structured_data['columns']]
                amount_cols = [col for col in columns if 'amount' in col]
                date_cols = [col for col in columns if 'date' in col]

                if len(amount_cols) >= 1 and len(date_cols) >= 1:
                    indicators_found.append(f"transaction_columns: {len(amount_cols)} amount, {len(date_cols)} date")
                    result["confidence"] = min(result["confidence"] + 0.4, 1.0)

        # Check for numbered transaction lists
        transaction_numbers = re.findall(r'\btransaction\s*\d+\b', text_lower, re.IGNORECASE)
        if len(transaction_numbers) > 2:
            indicators_found.append(f"numbered_transactions: {len(transaction_numbers)} found")
            result["confidence"] = min(result["confidence"] + 0.3, 1.0)

        # Check for multiple date-amount patterns
        date_amount_patterns = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}.*?\$?\d+\.?\d*', text)
        if len(date_amount_patterns) > 3:
            indicators_found.append(f"date_amount_patterns: {len(date_amount_patterns)} found")
            result["confidence"] = min(result["confidence"] + 0.25, 1.0)

        result["is_multi"] = result["confidence"] > 0.6
        result["indicators"] = indicators_found

        return result

    def _get_multi_transaction_variant(self, base_type: str) -> str:
        """
        Get the multi-transaction variant of a document type

        Args:
            base_type: Base document type

        Returns:
            Multi-transaction variant type
        """
        mapping = {
            DocumentType.BANK_STATEMENT.value: DocumentType.BANK_STATEMENT_MULTI.value,
            DocumentType.EXPENSE_REPORT.value: DocumentType.EXPENSE_REPORT_MULTI.value,
            DocumentType.CREDIT_CARD_STATEMENT.value: DocumentType.CREDIT_CARD_STATEMENT_MULTI.value,
        }

        return mapping.get(base_type, base_type)

    def get_supported_document_types(self) -> List[str]:
        """
        Get list of all supported document types

        Returns:
            List of document type strings
        """
        return [dt.value for dt in DocumentType]

    def get_multi_transaction_types(self) -> List[str]:
        """
        Get list of multi-transaction document types

        Returns:
            List of multi-transaction type strings
        """
        return [
            DocumentType.BANK_STATEMENT_MULTI.value,
            DocumentType.EXPENSE_REPORT_MULTI.value,
            DocumentType.CREDIT_CARD_STATEMENT_MULTI.value,
        ]