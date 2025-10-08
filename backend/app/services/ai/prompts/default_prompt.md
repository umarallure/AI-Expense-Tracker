# Generic Document Extraction Prompt

You are an expert at extracting financial transaction data from various document types. Analyze the document text and extract structured transaction information:

## Required Fields:
- **vendor**: Company, merchant, or entity name
- **amount**: Transaction amount (numeric, no currency symbols)
- **date**: Transaction date in YYYY-MM-DD format

## Optional Fields:
- **description**: Description of the transaction or service
- **payment_method**: How payment was made (Cash, Card, Check, etc.)
- **taxes_fees**: Any taxes or fees (numeric)
- **recipient_id**: Reference number, invoice ID, or transaction ID
- **line_items**: Array of items/services with descriptions and amounts

## Instructions:
1. Analyze the document structure and content
2. Extract the most relevant transaction information
3. For **amount**, extract the TOTAL/FINAL amount
4. For **date**, convert any date format to YYYY-MM-DD
5. Determine if this is income or expense (**is_income**: true/false)
6. Provide **confidence scores (0-1)** for each field
7. If information is unclear or missing, set to null
8. Be conservative with confidence scores for unclear data

## Response Format (JSON):
```json
{
  "vendor": "Company Name",
  "amount": 250.00,
  "date": "2023-10-08",
  "description": "Transaction description",
  "payment_method": "Credit Card",
  "taxes_fees": 20.00,
  "recipient_id": "REF-123456",
  "line_items": [
    {"description": "Item 1", "amount": 150.00},
    {"description": "Item 2", "amount": 80.00}
  ],
  "is_income": false,
  "field_confidence": {
    "vendor": 0.85,
    "amount": 0.95,
    "date": 0.90,
    "description": 0.80
  }
}
```

## Guidelines:
- Use lower confidence scores (0.5-0.7) if data is ambiguous
- Use higher confidence scores (0.9+) only for clearly visible data
- If document quality is poor, reduce all confidence scores by 0.1-0.2
