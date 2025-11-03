# Multi-Transaction Processing & AI Confidence Accuracy - Test Criteria

## Overview
This feature addresses the issue where multi-transaction documents (bank statements, expense reports, etc.) only process one transaction instead of extracting all transactions within the file.

## Test Scenarios

### 1. Excel File Processing
**Test Case 1.1: Bank Statement Excel File**
- **Input**: Excel file with 10 transactions (dates, amounts, descriptions, vendors)
- **Expected Output**: 10 separate transactions created
- **Validation**:
  - All 10 transactions extracted with correct vendor, amount, date
  - Each transaction linked to the same source document
  - Confidence scores calculated per transaction
  - No duplicate transactions

**Test Case 1.2: Expense Report Excel**
- **Input**: Excel with multiple expense entries across different categories
- **Expected Output**: Multiple transactions with appropriate categories
- **Validation**:
  - Category detection works for each transaction
  - Line items preserved where applicable
  - Tax calculations handled correctly

### 2. PDF Document Processing
**Test Case 2.1: Multi-Page Bank Statement PDF**
- **Input**: PDF with 15 transactions across multiple pages
- **Expected Output**: All 15 transactions extracted
- **Validation**:
  - Page breaks don't interrupt transaction detection
  - Running balances tracked correctly
  - Transaction sequence maintained

**Test Case 2.2: Invoice with Line Items**
- **Input**: Invoice PDF with multiple line items
- **Expected Output**: Single transaction with line items OR multiple transactions (configurable)
- **Validation**:
  - Line items correctly associated with main transaction
  - Subtotal and tax calculations accurate

### 3. AI Confidence Scoring Improvements
**Test Case 3.1: Missing Data Penalty**
- **Input**: Document with only 50% of transactions extracted
- **Expected Output**: Reduced confidence score reflecting incomplete extraction
- **Validation**:
  - Confidence score < 0.85 when multiple transactions missed
  - Clear indication of data completeness issues

**Test Case 3.2: Field-Level Confidence**
- **Input**: Document with mixed quality data (some fields clear, others ambiguous)
- **Expected Output**: Accurate field-level confidence scores
- **Validation**:
  - OCR quality affects confidence appropriately
  - Missing critical fields heavily penalized

### 4. Document Type Detection
**Test Case 4.1: Bank Statement Recognition**
- **Input**: Various bank statement formats
- **Expected Output**: Correctly classified as "bank_statement"
- **Validation**:
  - Triggers multi-transaction extraction mode
  - Appropriate AI prompts used

**Test Case 4.2: Single vs Multi-Transaction Classification**
- **Input**: Receipt vs Bank Statement
- **Expected Output**: Different processing paths
- **Validation**:
  - Receipts → single transaction
  - Statements → multi-transaction

### 5. Transaction Creation Logic
**Test Case 5.1: Bulk Transaction Creation**
- **Input**: 20 extracted transactions from one document
- **Expected Output**: 20 database records created
- **Validation**:
  - All transactions linked to source document
  - No duplicate prevention conflicts
  - Proper status assignment based on confidence

**Test Case 5.2: Confidence-Based Status**
- **Input**: Transactions with varying confidence scores
- **Expected Output**: Appropriate status assignment
- **Validation**:
  - High confidence → "approved" or "pending"
  - Low confidence → "draft" or flagged for review

### 6. Error Handling & Edge Cases
**Test Case 6.1: Malformed Excel Files**
- **Input**: Excel with missing headers or inconsistent data
- **Expected Output**: Graceful handling with appropriate error messages
- **Validation**:
  - Partial data extraction where possible
  - Clear error reporting for failed transactions

**Test Case 6.2: Large Files**
- **Input**: Excel/CSV with 1000+ transactions
- **Expected Output**: Efficient processing without timeouts
- **Validation**:
  - Memory usage within limits
  - Processing time acceptable (< 5 minutes)

### 7. Integration Testing
**Test Case 7.1: End-to-End Processing**
- **Input**: Upload multi-transaction file through UI
- **Expected Output**: All transactions visible in approvals/transactions list
- **Validation**:
  - UI correctly displays multiple transactions
  - Document linking works properly
  - Status indicators accurate

**Test Case 7.2: Duplicate Detection**
- **Input**: File with some duplicate transactions
- **Expected Output**: Duplicates flagged or prevented
- **Validation**:
  - Duplicate detection works across multiple transactions
  - User notified of potential duplicates

## Performance Benchmarks

### Processing Time
- **Small File** (10 transactions): < 30 seconds
- **Medium File** (100 transactions): < 2 minutes
- **Large File** (1000 transactions): < 5 minutes

### Accuracy Targets
- **Transaction Detection**: > 95% of transactions found
- **Field Extraction**: > 90% accuracy for required fields
- **Confidence Scoring**: > 85% correlation with manual review

## Configuration Options

### Multi-Transaction Settings
- **Max Transactions Per Document**: Configurable limit (default: 500)
- **Min Confidence Threshold**: Adjustable threshold for auto-creation
- **Processing Mode**: Single vs Multi-transaction extraction

### AI Processing Options
- **Batch Processing**: Process multiple transactions in single AI call
- **Sequential Processing**: Individual AI calls per transaction
- **Hybrid Approach**: Combine both methods based on document size