# Multi-Transaction Processing & AI Confidence Accuracy - Implementation Plan

## Executive Summary
Implement comprehensive multi-transaction document processing to extract all transactions from files like bank statements and expense reports, while improving AI confidence scoring to reflect data completeness rather than just OCR quality.

## Current Architecture Issues

### 1. Single Transaction Assumption
- All extractors and AI processing assume one transaction per document
- Bank statement prompt explicitly limits to "one transaction"
- Transaction creator only handles single transaction per document

### 2. Confidence Scoring Limitations
- Only considers field-level confidence, not data completeness
- Doesn't penalize for missing multiple transactions in multi-transaction documents
- High OCR confidence doesn't reflect missing transactional data

### 3. Excel Processing Limitations
- Detects transaction columns but processes entire sheet as one text blob
- No row-by-row transaction extraction

## Implementation Plan

### Phase 1: Core Multi-Transaction Detection (Week 1)

#### 1.1 Document Type Enhancement
**Objective**: Improve document classification to detect multi-transaction documents
**Changes**:
- Update `DocumentClassifier` to identify multi-transaction document types
- Add confidence scoring for multi-transaction detection
- Create new document types: `bank_statement_multi`, `expense_report_multi`

**Files to Modify**:
- `document_classifier.py`: Enhance classification logic
- Add new prompt templates for multi-transaction detection

#### 1.2 Excel Extractor Multi-Transaction Support
**Objective**: Enable Excel extractor to process multiple transactions
**Changes**:
- Modify `ExcelExtractor` to detect and extract individual transaction rows
- Add transaction row detection logic
- Create structured transaction data from spreadsheet rows

**Files to Modify**:
- `excel_extractor.py`: Add multi-transaction extraction logic
- Update `_dataframe_to_structured()` to return list of transactions

#### 1.3 AI Prompt Updates
**Objective**: Update AI prompts to handle multi-transaction documents
**Changes**:
- Create new prompt for multi-transaction extraction
- Update bank statement prompt to extract ALL transactions
- Add batch processing capabilities

**Files to Modify**:
- `prompts/bank_statement_prompt.md`: Remove single transaction limitation
- `prompts/multi_transaction_prompt.md`: New prompt for batch extraction
- `data_extractor.py`: Add multi-transaction processing logic

### Phase 2: Enhanced Confidence Scoring (Week 2)

#### 2.1 Data Completeness Scoring
**Objective**: Implement confidence scoring based on data completeness
**Changes**:
- Add transaction count validation
- Penalize for missing transactions in multi-transaction documents
- Create completeness ratio scoring

**Files to Modify**:
- `confidence_scorer.py`: Add data completeness calculations
- Update field weighting logic

#### 2.2 Multi-Transaction Validation
**Objective**: Validate that all expected transactions are extracted
**Changes**:
- Add transaction count estimation from document structure
- Compare extracted vs expected transaction counts
- Flag documents with suspiciously low extraction rates

**Files to Modify**:
- `data_extractor.py`: Add transaction count validation
- `document_processor.py`: Add completeness checking

### Phase 3: Transaction Creation Overhaul (Week 3)

#### 3.1 Multi-Transaction Creator
**Objective**: Enable creation of multiple transactions from one document
**Changes**:
- Modify `TransactionCreator` to handle transaction arrays
- Add batch transaction creation with proper linking
- Implement duplicate detection across multiple transactions

**Files to Modify**:
- `transaction_creator.py`: Add multi-transaction support
- Update database linking logic

#### 3.2 Document-Transaction Relationship
**Objective**: Properly link multiple transactions to source documents
**Changes**:
- Update document schema to support multiple transaction links
- Add transaction grouping for document relationships
- Implement proper cleanup on document deletion

**Files to Modify**:
- Database schema updates (if needed)
- Document service updates

### Phase 4: Integration & Testing (Week 4)

#### 4.1 End-to-End Integration
**Objective**: Integrate all components into cohesive pipeline
**Changes**:
- Update main document processing orchestrator
- Add configuration options for multi-transaction processing
- Implement processing mode selection (single vs multi)

**Files to Modify**:
- `document_processor.py`: Add multi-transaction routing
- Configuration updates

#### 4.2 Performance Optimization
**Objective**: Optimize for large multi-transaction files
**Changes**:
- Implement batch processing for AI calls
- Add memory-efficient processing for large files
- Implement progress tracking for long operations

**Files to Modify**:
- All extractor and AI service files
- Add progress tracking

#### 4.3 Comprehensive Testing
**Objective**: Test all scenarios and edge cases
**Changes**:
- Implement test suite based on test criteria
- Add performance benchmarking
- Create sample test files

**Files to Create**:
- `test_multi_transaction.py`: Comprehensive test suite
- Sample test files (Excel, PDF) with known transaction counts

## Technical Architecture Changes

### New Data Structures

#### MultiTransactionResult
```python
class MultiTransactionResult:
    def __init__(self):
        self.transactions: List[Dict[str, Any]] = []
        self.document_type: str = ""
        self.expected_transaction_count: int = 0
        self.extracted_transaction_count: int = 0
        self.completeness_score: float = 0.0
        self.overall_confidence: float = 0.0
```

#### TransactionBatch
```python
class TransactionBatch:
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.transactions: List[Dict[str, Any]] = []
        self.processing_status: str = "pending"
        self.created_transaction_ids: List[str] = []
```

### Configuration Options

#### Multi-Transaction Settings
```python
MULTI_TRANSACTION_CONFIG = {
    "max_transactions_per_document": 500,
    "min_confidence_threshold": 0.85,
    "batch_processing_enabled": True,
    "completeness_penalty_factor": 0.2,
    "processing_timeout_seconds": 300
}
```

### AI Processing Modes

#### 1. Single Transaction Mode (Current)
- One AI call per document
- Returns single transaction object

#### 2. Multi-Transaction Mode (New)
- AI analyzes document structure first
- Estimates transaction count
- Processes in batches or individually
- Returns array of transaction objects

#### 3. Hybrid Mode (Future)
- Small documents: single call
- Large documents: batch processing

## Risk Mitigation

### Performance Risks
- **Large File Processing**: Implement chunking and streaming
- **AI API Limits**: Add rate limiting and batch processing
- **Memory Usage**: Process in chunks, implement cleanup

### Accuracy Risks
- **False Positives**: Add validation layers
- **Missing Transactions**: Implement completeness checking
- **Duplicate Transactions**: Add deduplication logic

### Data Integrity Risks
- **Partial Failures**: Implement transaction rollback
- **Document Linking**: Ensure proper relationship management
- **Status Consistency**: Maintain consistent transaction states

## Success Metrics

### Functional Metrics
- **Extraction Accuracy**: >95% of transactions detected
- **Field Accuracy**: >90% for required fields
- **Processing Success Rate**: >98% for valid files

### Performance Metrics
- **Processing Time**: <2 minutes for 100 transactions
- **Memory Usage**: <500MB for large files
- **API Call Efficiency**: Minimize redundant AI calls

### Quality Metrics
- **Confidence Correlation**: >85% match with manual review
- **False Positive Rate**: <5% invalid transactions
- **User Satisfaction**: >90% approval rating

## Rollout Strategy

### Phase 1: Feature Flag Deployment
- Deploy behind feature flag
- Enable for beta users only
- Monitor performance and accuracy

### Phase 2: Gradual Rollout
- Enable for 25% of users
- A/B test with single-transaction processing
- Gather user feedback

### Phase 3: Full Deployment
- Enable for all users
- Update documentation
- Provide migration path for existing single-transaction documents

## Monitoring & Maintenance

### Key Metrics to Monitor
- Processing success rates by document type
- Average confidence scores
- Processing time distributions
- Error rates and types

### Alert Conditions
- Processing success rate drops below 95%
- Average processing time exceeds 5 minutes
- High error rates for specific document types

### Maintenance Tasks
- Regular prompt optimization based on performance data
- Model updates for improved accuracy
- Configuration tuning based on user feedback