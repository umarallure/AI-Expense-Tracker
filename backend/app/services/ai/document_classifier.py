"""
Document Classifier Service
Uses OpenAI GPT-4o-mini to classify document types with confidence scoring.
"""
from typing import Tuple, Dict, Any
import requests
import json
from app.core.config import get_settings
from loguru import logger

settings = get_settings()


class DocumentClassifier:
    """
    Classifies documents into predefined types using AI.
    
    Supported document types:
    - invoice: Commercial invoices from vendors
    - receipt: Purchase receipts from stores/restaurants
    - bank_statement: Bank account statements
    - credit_card_statement: Credit card statements
    - expense_report: Employee expense reports
    - handwritten_note: Handwritten notes/receipts
    - other: Unrecognized document types
    """
    
    # Supported document types
    DOCUMENT_TYPES = [
        "invoice",
        "receipt",
        "bank_statement",
        "credit_card_statement",
        "expense_report",
        "handwritten_note",
        "other"
    ]
    
    def __init__(self, api_key: str = None):
        """
        Initialize DocumentClassifier with OpenRouter API.
        
        Args:
            api_key: OpenRouter API key (optional, defaults to settings)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "openai/gpt-4o-mini"  # OpenRouter model format
        self.temperature = 0.2  # Low temperature for consistency
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/agenticfyai1-ai/ai-powered-expense-tracker",
            "X-Title": "AI Expense Tracker"
        }
        
    def classify(self, text: str, max_retries: int = 3) -> Tuple[str, float]:
        """
        Classify document type from extracted text.
        
        Args:
            text: Raw extracted text from document
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (document_type, confidence_score)
            
        Example:
            >>> classifier = DocumentClassifier()
            >>> doc_type, confidence = classifier.classify(invoice_text)
            >>> print(f"Type: {doc_type}, Confidence: {confidence}")
            Type: invoice, Confidence: 0.95
        """
        try:
            # Truncate text if too long (max 4000 chars for classification)
            text_preview = text[:4000] if len(text) > 4000 else text
            
            # Build classification prompt
            prompt = self._build_classification_prompt(text_preview)
            
            # Call OpenRouter API with retry logic
            for attempt in range(max_retries):
                try:
                    payload = {
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert document classifier for financial documents. Analyze the text and classify it into one of the predefined document types."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": self.temperature,
                        "max_tokens": 200
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload,
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    parsed_result = json.loads(content)
                    
                    document_type = parsed_result.get("document_type", "other")
                    confidence = float(parsed_result.get("confidence", 0.5))
                    reasoning = parsed_result.get("reasoning", "")
                    
                    # Validate document type
                    if document_type not in self.DOCUMENT_TYPES:
                        logger.warning(f"Invalid document type '{document_type}', defaulting to 'other'")
                        document_type = "other"
                        confidence = 0.3
                    
                    # Validate confidence score
                    confidence = max(0.0, min(1.0, confidence))
                    
                    logger.info(
                        f"Document classified as '{document_type}' with confidence {confidence:.2f}. "
                        f"Reasoning: {reasoning}"
                    )
                    
                    return document_type, confidence
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        raise
                    continue
                    
                except Exception as e:
                    logger.error(f"OpenAI API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        raise
                    continue
            
            # If all retries failed
            raise Exception("All retry attempts failed")
            
        except Exception as e:
            logger.error(f"Document classification failed: {str(e)}")
            return "other", 0.3  # Low confidence fallback
    
    def _build_classification_prompt(self, text: str) -> str:
        """
        Build the classification prompt for OpenAI.
        
        Args:
            text: Document text to classify
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Classify the following document text into one of these categories:

**Document Types:**
1. **invoice** - Commercial invoices from vendors/suppliers (includes invoice number, vendor info, line items, totals)
2. **receipt** - Purchase receipts from stores/restaurants (simpler format, single transaction)
3. **bank_statement** - Bank account statements (multiple transactions, account balance, period)
4. **credit_card_statement** - Credit card statements (charges, payments, balance, statement period)
5. **expense_report** - Employee expense reports (multiple expenses, totals, reimbursement info)
6. **handwritten_note** - Handwritten receipts or notes (OCR'd text, may be messy)
7. **other** - Any document that doesn't fit the above categories

**Document Text:**
{text}

**Instructions:**
- Analyze the structure, content, and format of the text
- Identify key indicators (invoice numbers, transaction lists, account numbers, etc.)
- Consider the vocabulary and terminology used
- Provide a confidence score between 0 and 1
- Explain your reasoning briefly

**Response Format (JSON):**
{{
  "document_type": "<one of the 7 types above>",
  "confidence": <float between 0 and 1>,
  "reasoning": "<brief explanation of classification>"
}}"""
        return prompt
    
    def classify_batch(self, texts: list[str]) -> list[Tuple[str, float]]:
        """
        Classify multiple documents in batch.
        
        Args:
            texts: List of document texts
            
        Returns:
            List of (document_type, confidence) tuples
        """
        results = []
        for text in texts:
            doc_type, confidence = self.classify(text)
            results.append((doc_type, confidence))
        return results
    
    def get_supported_types(self) -> list[str]:
        """
        Get list of supported document types.
        
        Returns:
            List of document type strings
        """
        return self.DOCUMENT_TYPES.copy()
