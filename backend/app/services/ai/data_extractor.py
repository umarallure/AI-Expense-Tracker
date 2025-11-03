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
        
        # Performance optimization settings
        self.max_batch_size = 10  # Maximum transactions per batch
        self.max_context_length = 2000  # Maximum context text length
        self.batch_timeout = 60  # Timeout for batch processing
        self.memory_cleanup_threshold = 50  # Clean up memory after processing this many transactions
        
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
        max_retries: int = 3,
        structured_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from document text.
        
        Args:
            text: Raw extracted text from document
            document_type: Type of document (invoice, receipt, etc.)
            business_id: Business ID for category matching
            supabase_client: Supabase client for fetching categories
            max_retries: Maximum number of retry attempts
            structured_data: Pre-structured data from extractor (for multi-transaction docs)
            
        Returns:
            Dictionary with extracted fields and confidence scores
            
        Example:
            >>> extractor = DataExtractor()
            >>> data = extractor.extract(invoice_text, "invoice", business_id, supabase)
            >>> print(data["amount"], data["vendor"], data["field_confidence"])
        """
        try:
            # Check if this is a multi-transaction document
            # Either from structured_data indicators or explicit force flag
            if structured_data and (
                self._is_multi_transaction_data(structured_data) or 
                structured_data.get("force_multi_transaction")
            ):
                # For forced multi-transaction mode (e.g., chunked bank statements),
                # create a minimal structured_data to trigger multi-transaction extraction
                if not structured_data.get("transactions"):
                    # Tell the AI to extract ALL transactions from this text
                    structured_data["transactions"] = "EXTRACT_ALL"
                
                return self._extract_multiple_transactions(
                    text, document_type, business_id, supabase_client, 
                    structured_data, max_retries
                )
            
            # Single transaction extraction (existing logic)
            return self._extract_single_transaction(
                text, document_type, business_id, supabase_client, max_retries
            )
            
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
            # Validate UUID format
            import uuid
            try:
                uuid.UUID(business_id)
            except (ValueError, AttributeError):
                logger.warning(f"Invalid business_id format: {business_id}, using empty categories")
                return []
            
            response = supabase_client.table("categories").select(
                "id, category_name, description"
            ).eq("business_id", business_id).execute()
            
            categories = []
            if response.data:
                for cat in response.data:
                    categories.append({
                        "id": cat["id"],
                        "name": cat["category_name"],
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
                f"- ID: {cat['id']}, Name: {cat['name']}, Description: {cat['description']}" if cat['description']
                else f"- ID: {cat['id']}, Name: {cat['name']}"
                for cat in categories
            ])
            category_instructions = f"""
## Available Categories (select ONE category_id):
{category_list}

**Category Selection Instructions:**
- Analyze the transaction and select the MOST APPROPRIATE category_id from the list above
- Return the category_id (UUID) that best matches the transaction
- Consider the vendor, description, and transaction type when selecting
- If no category fits well, you can leave category_id as null
"""
        else:
            category_instructions = """
## Category:
- No business categories available - leave category_id as null
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
        validated["category_id"] = self._clean_string(data.get("category_id"))
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
    
    def _clean_json_response(self, content: str) -> str:
        """
        Clean JSON response from AI to handle common formatting issues
        
        Args:
            content: Raw JSON string from AI
            
        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        # Strip whitespace
        content = content.strip()
        
        # Fix common JSON issues
        import re
        
        # Remove trailing commas before closing braces/brackets
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        # Fix missing commas between object properties (common AI error)
        # Look for patterns like: }"field": or ]"field":
        content = re.sub(r'([}\]])(\s*)("[\w_]+"\s*:)', r'\1,\2\3', content)
        
        # Fix missing commas between array elements
        # Look for patterns like: }{ or }{
        content = re.sub(r'(\})(\s*)(\{)', r'\1,\2\3', content)
        content = re.sub(r'(\])(\s*)(\[)', r'\1,\2\3', content)
        
        # Remove any non-JSON text before the first {
        if '{' in content:
            content = content[content.index('{'):]
        
        # Remove any non-JSON text after the last }
        if '}' in content:
            content = content[:content.rindex('}') + 1]
        
        return content
    
    def _clean_large_json_response(self, content: str) -> str:
        """
        Additional cleaning for large multi-transaction JSON responses
        
        Args:
            content: JSON string from AI
            
        Returns:
            Cleaned JSON string
        """
        import re
        
        # If response seems truncated (ends abruptly), try to complete it
        if not content.rstrip().endswith('}'):
            logger.warning("Response appears truncated, attempting to complete JSON structure")
            
            # Count open vs closed braces and brackets
            open_braces = content.count('{')
            close_braces = content.count('}')
            open_brackets = content.count('[')
            close_brackets = content.count(']')
            
            # If we're inside a transaction object, close it
            if content.rstrip().endswith(','):
                # Remove trailing comma
                content = content.rstrip().rstrip(',')
            
            # Close any incomplete strings
            if content.count('"') % 2 != 0:
                content += '"'
            
            # Close open structures
            missing_brackets = open_brackets - close_brackets
            missing_braces = open_braces - close_braces
            
            if missing_brackets > 0 or missing_braces > 0:
                logger.info(f"Closing {missing_brackets} brackets and {missing_braces} braces")
                content += ']' * missing_brackets
                content += '}' * missing_braces
        
        # Remove any incomplete transaction objects at the end
        # Look for patterns like: {"vendor": "ABC", "amount"
        # Find the last complete transaction
        last_complete_transaction = content.rfind('"}')
        if last_complete_transaction > 0:
            # Check if there's incomplete data after this
            after_last = content[last_complete_transaction + 2:].strip()
            if after_last and not after_last.startswith(',') and not after_last.startswith(']'):
                # Truncate at last complete transaction
                content = content[:last_complete_transaction + 2]
                logger.warning("Removed incomplete transaction data from end of response")
                # Close structures properly
                if '"transactions"' in content:
                    content += ']}'
                else:
                    content += '}'
        
        return content
    
    def _parse_json_with_fallback(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON with multiple fallback strategies
        
        Args:
            content: JSON string to parse
            
        Returns:
            Parsed dictionary or None if all strategies fail
        """
        import re
        
        # Strategy 1: Direct parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.debug(f"Direct JSON parsing failed at position {e.pos}: {e}")
            
            # Strategy 2: Try to find and fix the error location
            try:
                error_pos = e.pos
                if error_pos and error_pos > 100:
                    # Try parsing up to the error
                    truncated = content[:error_pos]
                    # Close any open braces/brackets
                    open_braces = truncated.count('{') - truncated.count('}')
                    open_brackets = truncated.count('[') - truncated.count(']')
                    truncated += '}' * open_braces + ']' * open_brackets
                    parsed = json.loads(truncated)
                    logger.warning(f"Successfully parsed truncated JSON up to position {error_pos}")
                    return parsed
            except Exception as truncate_error:
                logger.debug(f"Truncation strategy failed: {truncate_error}")
        except Exception as e:
            logger.debug(f"JSON parsing failed with unexpected error: {e}")
        
        # Strategy 3: Extract just the transactions array if it exists
        try:
            # Look for "transactions": [...]
            match = re.search(r'"transactions"\s*:\s*\[(.*?)\](?=\s*[,}])', content, re.DOTALL)
            if match:
                transactions_json = '[' + match.group(1) + ']'
                transactions = json.loads(transactions_json)
                return {
                    "extraction_type": "multi_transaction",
                    "transactions": transactions,
                    "document_type": "unknown",
                    "total_amount": 0.0
                }
        except:
            pass
        
        # Strategy 4: Try to extract key fields manually with regex
        try:
            result = {
                "extraction_type": "single_transaction",
                "vendor": None,
                "amount": None,
                "date": None,
                "category": None
            }
            
            # Extract vendor
            vendor_match = re.search(r'"vendor"\s*:\s*"([^"]*)"', content)
            if vendor_match:
                result["vendor"] = vendor_match.group(1)
            
            # Extract amount
            amount_match = re.search(r'"amount"\s*:\s*(-?[\d.]+)', content)
            if amount_match:
                result["amount"] = float(amount_match.group(1))
            
            # Extract date
            date_match = re.search(r'"date"\s*:\s*"([^"]*)"', content)
            if date_match:
                result["date"] = date_match.group(1)
            
            # Extract category
            category_match = re.search(r'"category"\s*:\s*"([^"]*)"', content)
            if category_match:
                result["category"] = category_match.group(1)
            
            # Return if we got at least vendor and amount
            if result["vendor"] and result["amount"]:
                logger.warning("Used regex fallback to extract data from malformed JSON")
                return result
        except Exception as fallback_error:
            logger.debug(f"Regex fallback failed: {fallback_error}")
        
        # All strategies failed
        return None
    
    def _is_multi_transaction_data(self, structured_data: Dict) -> bool:
        """
        Check if structured data indicates multiple transactions
        
        Args:
            structured_data: Structured data from extractor
            
        Returns:
            True if multi-transaction document
        """
        # Check for explicit multi-transaction indicators
        if structured_data.get("extraction_method") == "multi_transaction":
            return True
        
        if structured_data.get("document_type") == "multi_transaction_excel":
            return True
        
        # Check for transactions array
        transactions = structured_data.get("transactions", [])
        if isinstance(transactions, list) and len(transactions) > 1:
            return True
        
        return False
    
    def _extract_single_transaction(
        self,
        text: str,
        document_type: str,
        business_id: str,
        supabase_client: Client,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Extract single transaction (existing logic)
        
        Args:
            text: Document text
            document_type: Document type
            business_id: Business ID
            supabase_client: Supabase client
            max_retries: Max retry attempts
            
        Returns:
            Extracted transaction data
        """
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
                
                # Clean the content before parsing
                content = self._clean_json_response(content)
                
                # Try to parse JSON with multiple strategies
                extracted_data = self._parse_json_with_fallback(content)
                
                if not extracted_data:
                    raise json.JSONDecodeError("Failed to parse JSON with all strategies", content, 0)
                
                # Validate and clean extracted data
                validated_data = self._validate_extracted_data(extracted_data)
                
                logger.info(
                    f"Successfully extracted single transaction from {document_type}. "
                    f"Fields extracted: {list(validated_data.keys())}"
                )
                
                return validated_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response (attempt {attempt + 1}/{max_retries}): {e}")
                # Log the problematic content for debugging
                try:
                    logger.debug(f"Problematic JSON content: {content[:500]}...")
                except:
                    pass
                if attempt == max_retries - 1:
                    # Return empty result instead of raising
                    logger.error("All JSON parsing attempts failed, returning empty result")
                    return self._get_empty_extraction_result("Failed to parse AI response")
                continue
                
            except Exception as e:
                logger.error(f"OpenAI API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    # Return empty result instead of raising
                    logger.error("All API call attempts failed, returning empty result")
                    return self._get_empty_extraction_result(f"API call failed: {str(e)}")
                continue
        
        # If all retries failed (should not reach here but safety net)
        return self._get_empty_extraction_result("All retry attempts failed")
    
    def _extract_all_transactions_from_text(
        self,
        text: str,
        document_type: str,
        business_id: str,
        supabase_client: Client,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Extract ALL transactions directly from text using AI (for chunked multi-transaction documents)
        
        Args:
            text: Raw text chunk
            document_type: Document type
            business_id: Business ID
            supabase_client: Supabase client
            max_retries: Max retry attempts
            
        Returns:
            Multi-transaction extraction result with transactions array
        """
        try:
            # Fetch business categories for intelligent matching
            categories = self._fetch_business_categories(business_id, supabase_client)
            
            # Build base prompt
            base_prompt = self._build_extraction_prompt(text, document_type, categories)
            
            # Enhanced multi-transaction instructions
            enhanced_instructions = """

## CRITICAL MULTI-TRANSACTION EXTRACTION RULES:

1. **Extract EVERY transaction** - Do not summarize or aggregate. Each row/line item is a separate transaction.
2. **One transaction per row** - If you see a table with 50 rows, extract 50 separate transactions.
3. **Required format** - Return valid JSON with a "transactions" array containing ALL transaction objects.
4. **No truncation** - Do not use "..." or skip transactions. Include every single one.

## JSON OUTPUT FORMAT (REQUIRED):

```json
{
  "transactions": [
    {
      "vendor": "Company Name",
      "amount": -100.50,
      "date": "2025-11-02",
      "description": "Transaction details",
      "category_id": null,
      "payment_method": "Debit Card",
      "is_income": false,
      "field_confidence": {
        "vendor": 0.95,
        "amount": 0.99,
        "date": 0.90
      }
    }
  ]
}
```

## VALIDATION CHECKLIST:
- [ ] JSON is valid and properly formatted
- [ ] All braces {} and brackets [] are closed
- [ ] No trailing commas before closing braces
- [ ] Each transaction has vendor, amount, and date
- [ ] Transactions array contains ALL found transactions
- [ ] No text outside the JSON structure

**START YOUR RESPONSE WITH THE JSON OBJECT. DO NOT INCLUDE ANY EXPLANATORY TEXT BEFORE OR AFTER THE JSON.**
"""
            
            prompt = base_prompt + enhanced_instructions
            
            # Call AI with enhanced configuration
            for attempt in range(max_retries):
                try:
                    payload = {
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": """You are a financial document extraction expert. Your task is to extract ALL transactions from documents and return them as valid JSON.

CRITICAL RULES:
1. Extract EVERY transaction found - no summarization
2. Return ONLY valid JSON - no explanatory text
3. Use the exact format specified in the prompt
4. Ensure all JSON syntax is correct (no trailing commas, all braces closed)
5. If you see 100 transaction rows, extract all 100 transactions

Your response must be parseable by json.loads() in Python."""
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.1,  # Lower temperature for more consistent JSON
                        "max_tokens": 8000,  # Increased for multi-transaction responses
                        "response_format": {"type": "json_object"}
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload,
                        timeout=90  # Increased timeout for large responses
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Log response length for debugging
                    logger.debug(f"AI response length: {len(content)} characters")
                    
                    # Check if response was truncated
                    if len(content) > 7000:
                        logger.warning(f"Large response detected ({len(content)} chars), may be truncated")
                    
                    # Clean and parse JSON with enhanced strategies
                    content = self._clean_json_response(content)
                    
                    # Additional cleaning for multi-transaction responses
                    content = self._clean_large_json_response(content)
                    
                    extracted_data = self._parse_json_with_fallback(content)
                    
                    if not extracted_data:
                        raise json.JSONDecodeError("Failed to parse JSON with all strategies", content, 0)
                    
                    # Ensure it's in multi-transaction format
                    if "transactions" not in extracted_data:
                        # Convert single transaction to multi-transaction format
                        extracted_data = {
                            "extraction_type": "multi_transaction",
                            "transactions": [extracted_data],
                            "document_type": document_type
                        }
                    else:
                        extracted_data["extraction_type"] = "multi_transaction"
                        extracted_data["document_type"] = document_type
                    
                    transactions = extracted_data.get("transactions", [])
                    logger.info(f"Successfully extracted {len(transactions)} transactions from text")
                    
                    # If we got 0 transactions and text is large, it might be too big for AI
                    if len(transactions) == 0 and len(text) > 4000:
                        logger.warning(f"No transactions extracted from large text ({len(text)} chars). May need smaller chunks.")
                    
                    return extracted_data
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response (attempt {attempt + 1}/{max_retries}): {e}")
                    
                    # On JSON errors, try with more aggressive prompt
                    if attempt < max_retries - 1:
                        logger.info("Retrying with simplified extraction...")
                        # Reduce chunk size hint in payload for next attempt
                        payload["max_tokens"] = 6000  # Reduce to prevent truncation
                        payload["messages"][0]["content"] += "\n\nIMPORTANT: If there are too many transactions, extract the first 20-30 complete transactions with full detail rather than trying to extract all with incomplete data."
                    
                    if attempt == max_retries - 1:
                        logger.error("All JSON parsing attempts failed, returning empty multi-transaction result")
                        return {
                            "extraction_type": "multi_transaction",
                            "transactions": [],
                            "error": "Failed to parse AI response"
                        }
                    continue
                    
                except Exception as e:
                    logger.error(f"AI extraction failed (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        return {
                            "extraction_type": "multi_transaction",
                            "transactions": [],
                            "error": str(e)
                        }
                    continue
            
            # Fallback
            return {
                "extraction_type": "multi_transaction",
                "transactions": [],
                "error": "All retry attempts failed"
            }
            
        except Exception as e:
            logger.error(f"Multi-transaction extraction from text failed: {str(e)}")
            return {
                "extraction_type": "multi_transaction",
                "transactions": [],
                "error": str(e)
            }
    
    def _extract_multiple_transactions(
        self,
        text: str,
        document_type: str,
        business_id: str,
        supabase_client: Client,
        structured_data: Dict,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Extract multiple transactions from structured data
        
        Args:
            text: Raw document text
            document_type: Document type
            business_id: Business ID
            supabase_client: Supabase client
            structured_data: Pre-structured data with transactions
            max_retries: Max retry attempts
            
        Returns:
            Multi-transaction extraction result
        """
        try:
            # Get pre-extracted transactions from structured data
            raw_transactions = structured_data.get("transactions", [])
            
            # Handle "EXTRACT_ALL" mode for chunked documents
            if raw_transactions == "EXTRACT_ALL" or not raw_transactions:
                logger.info("Using AI to extract all transactions from text (no pre-structured data)")
                # Use AI to extract transactions directly from text
                return self._extract_all_transactions_from_text(
                    text, document_type, business_id, supabase_client, max_retries
                )
            
            # Process transactions in batches to avoid token limits
            batch_size = min(self.max_batch_size, len(raw_transactions))  # Adaptive batch size
            processed_transactions = []
            total_batches = (len(raw_transactions) + batch_size - 1) // batch_size
            
            for batch_idx, i in enumerate(range(0, len(raw_transactions), batch_size)):
                batch = raw_transactions[i:i + batch_size]
                logger.info(f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch)} transactions)")
                
                batch_result = self._process_transaction_batch(
                    batch, text, document_type, business_id, supabase_client, max_retries
                )
                processed_transactions.extend(batch_result)
                
                # Memory cleanup for large datasets
                if len(processed_transactions) >= self.memory_cleanup_threshold:
                    # Force garbage collection hint (optional)
                    import gc
                    gc.collect()
                    logger.debug("Performed memory cleanup after processing large batch")
            
            # Calculate overall statistics
            total_transactions = len(processed_transactions)
            valid_transactions = [t for t in processed_transactions if t.get("vendor") and t.get("amount")]
            
            completeness_score = len(valid_transactions) / len(raw_transactions) if raw_transactions else 0
            
            result = {
                "extraction_type": "multi_transaction",
                "total_raw_transactions": len(raw_transactions),
                "total_processed_transactions": total_transactions,
                "valid_transactions": len(valid_transactions),
                "completeness_score": completeness_score,
                "transactions": processed_transactions,
                "document_type": document_type,
                "extraction_method": "batch_processing"
            }
            
            logger.info(
                f"Multi-transaction extraction completed. "
                f"Raw: {len(raw_transactions)}, Processed: {total_transactions}, "
                f"Valid: {len(valid_transactions)}, Completeness: {completeness_score:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Multi-transaction extraction failed: {str(e)}")
            # Fallback to single transaction extraction
            return self._extract_single_transaction(text, document_type, business_id, supabase_client, max_retries)
    
    def _process_transaction_batch(
        self,
        transaction_batch: List[Dict],
        full_text: str,
        document_type: str,
        business_id: str,
        supabase_client: Client,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of transactions using AI
        
        Args:
            transaction_batch: List of raw transaction data
            full_text: Full document text for context
            document_type: Document type
            business_id: Business ID
            supabase_client: Supabase client
            max_retries: Max retry attempts
            
        Returns:
            List of processed transactions
        """
        try:
            # Fetch business categories
            categories = self._fetch_business_categories(business_id, supabase_client)
            
            # Build batch processing prompt
            prompt = self._build_batch_extraction_prompt(
                transaction_batch, full_text, document_type, categories
            )
            
            # Call AI API
            for attempt in range(max_retries):
                try:
                    payload = {
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert at processing batches of financial transactions. Clean, validate, and enrich transaction data while providing confidence scores."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": self.temperature,
                        "max_tokens": 3000  # Larger limit for batch processing
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload,
                        timeout=self.batch_timeout  # Use configurable timeout
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    batch_result = json.loads(content)
                    
                    # Extract and validate transactions
                    processed_batch = self._validate_batch_result(batch_result, transaction_batch)
                    
                    logger.debug(f"Processed batch of {len(transaction_batch)} transactions")
                    
                    return processed_batch
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse batch JSON response (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        raise
                    continue
                    
                except Exception as e:
                    logger.error(f"Batch AI API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        raise
                    continue
            
            # If all retries failed, return original batch with minimal processing
            logger.warning("Batch processing failed, returning original data with basic validation")
            return [self._validate_extracted_data(tx) for tx in transaction_batch]
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            # Return original batch with minimal validation
            return [self._validate_extracted_data(tx) for tx in transaction_batch]
    
    def _build_batch_extraction_prompt(
        self,
        transactions: List[Dict],
        full_text: str,
        document_type: str,
        categories: List[Dict[str, str]]
    ) -> str:
        """
        Build prompt for batch transaction processing
        
        Args:
            transactions: List of raw transactions
            full_text: Full document text
            document_type: Document type
            categories: Available categories
            
        Returns:
            Formatted prompt
        """
        # Build category list
        category_list = "\n".join([
            f"- ID: {cat['id']}, Name: {cat['name']}" 
            for cat in categories
        ]) if categories else "No categories available"
        
        # Format transactions for AI
        transactions_text = "\n".join([
            f"Transaction {i+1}: {json.dumps(tx, default=str)}"
            for i, tx in enumerate(transactions)
        ])
        
        # Truncate full text if too long
        context_text = full_text[:self.max_context_length] if len(full_text) > self.max_context_length else full_text
        
        prompt = f"""Process this batch of {len(transactions)} transactions extracted from a {document_type} document.

AVAILABLE CATEGORIES:
{category_list}

DOCUMENT CONTEXT:
{context_text}

RAW TRANSACTIONS TO PROCESS:
{transactions_text}

INSTRUCTIONS:
1. For each transaction, clean and validate the data
2. Assign appropriate category_id from the available categories
3. Determine if each transaction is income (is_income: true) or expense (is_income: false)
4. Provide confidence scores for each field
5. Fill in missing vendor names from descriptions when possible
6. Ensure dates are in YYYY-MM-DD format
7. Ensure amounts are numeric (remove currency symbols)

RESPONSE FORMAT:
{{
  "transactions": [
    {{
      "original_index": 0,
      "vendor": "Clean Vendor Name",
      "amount": 123.45,
      "date": "2023-10-15",
      "description": "Clean description",
      "category_id": "category-uuid",
      "is_income": false,
      "field_confidence": {{
        "vendor": 0.85,
        "amount": 0.95,
        "date": 0.90
      }}
    }},
    ... more transactions
  ]
}}

Return ONLY valid JSON. Process all {len(transactions)} transactions."""
        
        return prompt
    
    def _validate_batch_result(self, batch_result: Dict, original_batch: List[Dict]) -> List[Dict[str, Any]]:
        """
        Validate and clean batch processing results
        
        Args:
            batch_result: Raw AI response
            original_batch: Original transaction batch
            
        Returns:
            List of validated transactions
        """
        processed_transactions = batch_result.get("transactions", [])
        
        # Ensure we have the right number of transactions
        if len(processed_transactions) != len(original_batch):
            logger.warning(
                f"Batch result count mismatch: expected {len(original_batch)}, "
                f"got {len(processed_transactions)}"
            )
        
        validated_transactions = []
        
        for i, tx in enumerate(processed_transactions):
            try:
                # Validate the transaction data
                validated_tx = self._validate_extracted_data(tx)
                
                # Preserve original index if available
                if isinstance(tx, dict) and "original_index" in tx:
                    validated_tx["_original_index"] = tx["original_index"]
                
                validated_transactions.append(validated_tx)
                
            except Exception as e:
                logger.error(f"Failed to validate transaction {i}: {str(e)}")
                # Add a minimal valid transaction
                validated_transactions.append(self._get_empty_extraction_result(f"Validation failed: {str(e)}"))
        
        return validated_transactions
    
    def _get_empty_extraction_result(self, error_message: str = "") -> Dict[str, Any]:
        """
        Get empty extraction result for error cases
        
        Args:
            error_message: Optional error message
            
        Returns:
            Empty extraction result dictionary
        """
        return {
            "vendor": None,
            "amount": None,
            "date": None,
            "description": error_message if error_message else None,
            "category_id": None,
            "payment_method": None,
            "taxes_fees": None,
            "recipient_id": None,
            "is_income": False,
            "line_items": [],
            "field_confidence": {
                "vendor": 0.0,
                "amount": 0.0,
                "date": 0.0
            }
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
