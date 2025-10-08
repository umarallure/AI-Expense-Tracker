"""
Data Extractor Service
Uses OpenAI GPT-4o-mini to extract structured transaction data from documents.
Includes dynamic category matching with business categories.
"""
from typing import Dict, Any, Optional, List
import requests
import json
from pathlib import Path
from app.core.config import get_settings
from supabase import Client
from loguru import logger

settings = get_settings()


class DataExtractor:
    """
    Extract structured transaction data from document text using AI.
    
    Features:
    - Document-type-specific prompts
    - Dynamic category matching with business categories
    - Field-level confidence scoring
    - JSON response validation
    - Handles missing fields gracefully
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize DataExtractor with OpenRouter API.
        
        Args:
            api_key: OpenRouter API key (optional, defaults to settings)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "openai/gpt-4o-mini"  # OpenRouter model format
        self.temperature = 0.25  # Low temperature for consistency
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/agenticfyai1-ai/ai-powered-expense-tracker",
            "X-Title": "AI Expense Tracker"
        }
        
    def extract(
        self,
        text: str,
        document_type: str,
        business_id: str,
        supabase_client: Client,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Extract structured data from document text.
        
        Args:
            text: Raw extracted text from document
            document_type: Type of document (invoice, receipt, etc.)
            business_id: Business ID for category matching
            supabase_client: Supabase client for fetching categories
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with extracted fields and confidence scores
            
        Example:
            >>> extractor = DataExtractor()
            >>> data = extractor.extract(invoice_text, "invoice", business_id, supabase)
            >>> print(data["amount"], data["vendor"], data["field_confidence"])
        """
        try:
            # Fetch business categories for dynamic matching
            categories = self._fetch_business_categories(business_id, supabase_client)
            
            # Get document-type-specific prompt
            prompt = self._build_extraction_prompt(text, document_type, categories)
            
            # Call OpenRouter API with retry logic
            for attempt in range(max_retries):
                try:
                    payload = {
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert at extracting structured financial data from documents. Extract information accurately and provide confidence scores for each field."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": self.temperature,
                        "max_tokens": 2000
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
                    extracted_data = json.loads(content)
                    
                    # Validate and clean extracted data
                    validated_data = self._validate_extracted_data(extracted_data)
                    
                    logger.info(
                        f"Successfully extracted data from {document_type}. "
                        f"Fields extracted: {list(validated_data.keys())}"
                    )
                    
                    return validated_data
                    
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
            logger.error(f"Data extraction failed: {str(e)}")
            return self._get_empty_extraction_result(str(e))
    
    def _fetch_business_categories(
        self,
        business_id: str,
        supabase_client: Client
    ) -> List[Dict[str, str]]:
        """
        Fetch categories for the business to enable dynamic category matching.
        
        Args:
            business_id: Business ID
            supabase_client: Supabase client
            
        Returns:
            List of category dictionaries with id and name
        """
        try:
            response = supabase_client.table("categories").select(
                "id, name, description"
            ).eq("business_id", business_id).execute()
            
            categories = []
            if response.data:
                for cat in response.data:
                    categories.append({
                        "id": cat["id"],
                        "name": cat["name"],
                        "description": cat.get("description", "")
                    })
            
            logger.debug(f"Fetched {len(categories)} categories for business {business_id}")
            return categories
            
        except Exception as e:
            logger.error(f"Failed to fetch categories: {str(e)}")
            return []
    
    def _build_extraction_prompt(
        self,
        text: str,
        document_type: str,
        categories: List[Dict[str, str]]
    ) -> str:
        """
        Build extraction prompt with document-type-specific instructions.
        
        Args:
            text: Document text
            document_type: Type of document
            categories: Available business categories
            
        Returns:
            Formatted prompt string
        """
        # Load document-type-specific prompt template
        prompt_file = self.prompts_dir / f"{document_type}_prompt.md"
        if not prompt_file.exists():
            # Fallback to default prompt
            prompt_file = self.prompts_dir / "default_prompt.md"
        
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except Exception as e:
            logger.warning(f"Failed to load prompt file: {e}. Using basic prompt.")
            prompt_template = self._get_basic_prompt_template()
        
        # Build category list for AI
        if categories:
            category_list = "\n".join([
                f"- {cat['name']}: {cat['description']}" if cat['description']
                else f"- {cat['name']}"
                for cat in categories
            ])
            category_instructions = f"""
## Available Categories (match to one of these):
{category_list}

**Category Matching Instructions:**
- Analyze the transaction and select the MOST APPROPRIATE category from the list above
- Use the category NAME exactly as shown
- If no category fits well, use "Uncategorized" or leave blank
- Consider the vendor, description, and transaction type when selecting
"""
        else:
            category_instructions = """
## Category:
- Provide a generic category suggestion (e.g., "Office Supplies", "Travel", "Meals")
- This will be mapped to business categories later
"""
        
        # Truncate text if too long (max 8000 chars for extraction)
        text_preview = text[:8000] if len(text) > 8000 else text
        
        # Build final prompt
        final_prompt = f"""{prompt_template}

{category_instructions}

---

## DOCUMENT TEXT TO ANALYZE:
```
{text_preview}
```

---

**Remember:**
1. Extract ALL available fields from the document
2. Provide confidence scores for each field (0.0 to 1.0)
3. For the **category** field, choose from the available categories list
4. Use null for any field that cannot be found
5. Ensure all amounts are numeric (no currency symbols)
6. Ensure all dates are in YYYY-MM-DD format
7. Return ONLY valid JSON, no additional text
"""
        return final_prompt
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted data.
        
        Args:
            data: Raw extracted data from AI
            
        Returns:
            Validated and cleaned data
        """
        validated = {}
        
        # Required fields
        validated["vendor"] = self._clean_string(data.get("vendor"))
        validated["amount"] = self._clean_amount(data.get("amount"))
        validated["date"] = self._clean_date(data.get("date"))
        
        # Optional fields
        validated["description"] = self._clean_string(data.get("description"))
        validated["category"] = self._clean_string(data.get("category"))
        validated["payment_method"] = self._clean_string(data.get("payment_method"))
        validated["taxes_fees"] = self._clean_amount(data.get("taxes_fees"))
        validated["recipient_id"] = self._clean_string(data.get("recipient_id"))
        validated["is_income"] = bool(data.get("is_income", False))
        
        # Line items
        validated["line_items"] = self._clean_line_items(data.get("line_items", []))
        
        # Field confidence scores
        validated["field_confidence"] = self._clean_confidence_scores(
            data.get("field_confidence", {})
        )
        
        return validated
    
    def _clean_string(self, value: Any) -> Optional[str]:
        """Clean and validate string field"""
        if value is None or value == "":
            return None
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()
    
    def _clean_amount(self, value: Any) -> Optional[float]:
        """Clean and validate amount field"""
        if value is None:
            return None
        try:
            # Remove currency symbols and commas
            if isinstance(value, str):
                value = value.replace("$", "").replace(",", "").strip()
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid amount value: {value}")
            return None
    
    def _clean_date(self, value: Any) -> Optional[str]:
        """Clean and validate date field"""
        if value is None or value == "":
            return None
        # Basic validation - should be YYYY-MM-DD format
        if isinstance(value, str) and len(value) == 10:
            return value
        logger.warning(f"Invalid date format: {value}")
        return None
    
    def _clean_line_items(self, items: Any) -> List[Dict[str, Any]]:
        """Clean and validate line items"""
        if not items or not isinstance(items, list):
            return []
        
        cleaned_items = []
        for item in items:
            if isinstance(item, dict):
                cleaned_item = {
                    "description": self._clean_string(item.get("description")),
                    "amount": self._clean_amount(item.get("amount"))
                }
                if cleaned_item["description"] or cleaned_item["amount"]:
                    cleaned_items.append(cleaned_item)
        
        return cleaned_items
    
    def _clean_confidence_scores(self, scores: Any) -> Dict[str, float]:
        """Clean and validate confidence scores"""
        if not scores or not isinstance(scores, dict):
            return {}
        
        cleaned_scores = {}
        for field, score in scores.items():
            try:
                score_float = float(score)
                # Clamp between 0 and 1
                cleaned_scores[field] = max(0.0, min(1.0, score_float))
            except (ValueError, TypeError):
                logger.warning(f"Invalid confidence score for {field}: {score}")
                cleaned_scores[field] = 0.5  # Default to medium confidence
        
        return cleaned_scores
    
    def _get_empty_extraction_result(self, error: str) -> Dict[str, Any]:
        """Return empty extraction result on failure"""
        return {
            "vendor": None,
            "amount": None,
            "date": None,
            "description": None,
            "category": None,
            "payment_method": None,
            "taxes_fees": None,
            "recipient_id": None,
            "is_income": False,
            "line_items": [],
            "field_confidence": {},
            "extraction_error": error
        }
    
    def _get_basic_prompt_template(self) -> str:
        """Fallback basic prompt template"""
        return """Extract structured financial transaction data from the document text below.

Extract these fields:
- vendor: Company/merchant name
- amount: Total amount (numeric)
- date: Transaction date (YYYY-MM-DD)
- description: Brief description
- payment_method: Payment method used
- taxes_fees: Tax amount (numeric)
- recipient_id: Reference/invoice number
- is_income: true/false
- line_items: Array of items with description and amount
- field_confidence: Confidence scores for each field (0-1)

Return ONLY valid JSON format."""
