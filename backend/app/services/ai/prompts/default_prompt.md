# Generic Document Multi-Transaction Extraction Prompt

You are an expert at extracting financial transaction data from various document types. Analyze the document text and extract ALL structured transaction information found:

## Required Fields per Transaction:
- **vendor**: Company, merchant, or entity name
- **amount**: Transaction amount (numeric, no currency symbols, negative for expenses)
- **date**: Transaction date in YYYY-MM-DD format

## Optional Fields per Transaction:
- **description**: Description of the transaction or service
- **category_id**: UUID of the transaction category (select from available categories)
- **payment_method**: How payment was made (Cash, Card, Check, etc.)
- **taxes_fees**: Any taxes or fees (numeric)
- **recipient_id**: Reference number, invoice ID, or transaction ID
- **line_items**: Array of items/services with descriptions and amounts

## Special Instructions:
1. Documents can contain MULTIPLE transactions - extract ALL transactions found
2. Analyze the document structure and content thoroughly
3. For **amount**, use negative values for expenses (standard accounting convention)
4. For **category_id**, select the most appropriate category UUID from the available categories list
5. For **date**, convert any date format to YYYY-MM-DD
6. Determine if each transaction is income or expense (**is_income**: true/false)
7. Provide **confidence scores (0-1)** for each field of each transaction
8. Return ALL transactions found, not just the most prominent one
9. If information is unclear or missing, set to null
10. Be conservative with confidence scores for unclear data

## Response Format (JSON):
```json
{
  "transactions": [
    {
      "vendor": "Company Name",
      "amount": -250.00,
      "date": "2023-10-08",
      "description": "Transaction description",
      "category_id": "07f30fb6-bb8a-4e90-87e6-40dbcc86240b",
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
        "category_id": 0.80,
        "description": 0.80
      }
    },
    {
      "vendor": "Another Company",
      "amount": 500.00,
      "date": "2023-10-09",
      "description": "Income transaction",
      "category_id": "income-category-uuid",
      "payment_method": "Bank Transfer",
      "recipient_id": "INC-789012",
      "is_income": true,
      "field_confidence": {
        "vendor": 0.90,
        "amount": 0.98,
        "date": 0.95,
        "category_id": 0.85
      }
    }
  ]
}
```

## Important Notes:
- Extract EVERY transaction found in the document
- Do not limit to one transaction - documents often contain multiple entries
- Each transaction should be a separate object in the transactions array
- If no transactions are found, return an empty transactions array
- Maintain the chronological order of transactions as they appear in the document

## Guidelines:
- Use lower confidence scores (0.5-0.7) if data is ambiguous
- Use higher confidence scores (0.9+) only for clearly visible data
- If document quality is poor, reduce all confidence scores by 0.1-0.2
- For **category**, consider: Travel (hotels, flights), Meals (restaurants), Office Supplies (stationery), Professional Services (consulting), etc.
