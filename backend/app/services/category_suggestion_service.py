"""
Smart Category Suggestion Service
Uses AI to analyze transaction patterns and suggest appropriate categories based on description, vendor, and amount.
Provides confidence scores and learns from user corrections over time.
"""
from typing import Dict, Any, List, Optional, Tuple
import requests
import json
from pathlib import Path
from collections import defaultdict, Counter
from loguru import logger
from supabase import Client
from app.core.config import get_settings

settings = get_settings()


class CategorySuggestionService:
    """
    Service for intelligent category suggestions using AI analysis.

    Features:
    - AI-powered pattern recognition for transaction categorization
    - Confidence scoring based on multiple factors
    - Learning from user corrections and historical patterns
    - Vendor-based categorization patterns
    - Amount-range based suggestions
    - Description keyword analysis
    """

    def __init__(self, api_key: str = None):
        """
        Initialize CategorySuggestionService with OpenRouter API.

        Args:
            api_key: OpenRouter API key (optional, defaults to settings)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "openai/gpt-4o-mini"
        self.temperature = 0.3  # Low temperature for consistency
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/agenticfyai1-ai/ai-powered-expense-tracker",
            "X-Title": "AI Expense Tracker"
        }

    async def suggest_categories(
        self,
        transactions: List[Dict[str, Any]],
        business_id: str,
        supabase_client: Client,
        include_historical_patterns: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Suggest categories for multiple transactions.

        Args:
            transactions: List of transaction data
            business_id: Business ID for category matching
            supabase_client: Supabase client
            include_historical_patterns: Whether to include historical categorization patterns

        Returns:
            List of suggestions with confidence scores
        """
        try:
            # Fetch available categories
            categories = await self._fetch_business_categories(business_id, supabase_client)

            if not categories:
                logger.warning(f"No categories found for business {business_id}")
                return []

            # Get historical patterns if requested
            historical_patterns = {}
            if include_historical_patterns:
                historical_patterns = await self._get_historical_patterns(business_id, supabase_client)

            suggestions = []

            for transaction in transactions:
                suggestion = await self._suggest_single_category(
                    transaction, categories, historical_patterns, supabase_client
                )
                if suggestion:
                    suggestions.append(suggestion)

            logger.info(f"Generated {len(suggestions)} category suggestions for {len(transactions)} transactions")
            return suggestions

        except Exception as e:
            logger.error(f"Failed to generate category suggestions: {str(e)}")
            return []

    async def suggest_category_for_transaction(
        self,
        transaction: Dict[str, Any],
        business_id: str,
        supabase_client: Client
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest a category for a single transaction.

        Args:
            transaction: Transaction data
            business_id: Business ID
            supabase_client: Supabase client

        Returns:
            Category suggestion with confidence score
        """
        try:
            categories = await self._fetch_business_categories(business_id, supabase_client)
            historical_patterns = await self._get_historical_patterns(business_id, supabase_client)

            return await self._suggest_single_category(
                transaction, categories, historical_patterns, supabase_client
            )

        except Exception as e:
            logger.error(f"Failed to suggest category for transaction: {str(e)}")
            return None

    async def _suggest_single_category(
        self,
        transaction: Dict[str, Any],
        categories: List[Dict[str, Any]],
        historical_patterns: Dict[str, Any],
        supabase_client: Client
    ) -> Optional[Dict[str, Any]]:
        """
        Generate category suggestion for a single transaction.

        Args:
            transaction: Transaction data
            categories: Available categories
            historical_patterns: Historical categorization patterns
            supabase_client: Supabase client

        Returns:
            Category suggestion or None
        """
        try:
            # Skip if transaction already has a category
            if transaction.get("category_id"):
                return None

            transaction_id = transaction.get("id")
            description = transaction.get("description", "")
            vendor = transaction.get("vendor", "")
            amount = transaction.get("amount", 0)
            is_income = transaction.get("is_income", False)

            # Filter categories by type (income/expense)
            filtered_categories = [
                cat for cat in categories
                if cat.get("category_type") == ("income" if is_income else "expense")
            ]

            if not filtered_categories:
                return None

            # Check historical patterns first
            historical_match = self._find_historical_match(
                description, vendor, amount, historical_patterns, filtered_categories
            )

            if historical_match and historical_match["confidence"] >= 0.8:
                return {
                    "transaction_id": transaction_id,
                    "suggested_category_id": historical_match["category_id"],
                    "suggested_category_name": historical_match["category_name"],
                    "confidence_score": historical_match["confidence"],
                    "reason": historical_match["reason"],
                    "suggestion_type": "historical_pattern"
                }

            # Use AI for intelligent suggestion
            ai_suggestion = await self._get_ai_category_suggestion(
                description, vendor, amount, is_income, filtered_categories
            )

            if ai_suggestion:
                return {
                    "transaction_id": transaction_id,
                    "suggested_category_id": ai_suggestion["category_id"],
                    "suggested_category_name": ai_suggestion["category_name"],
                    "confidence_score": ai_suggestion["confidence"],
                    "reason": ai_suggestion["reason"],
                    "suggestion_type": "ai_analysis"
                }

            # Fallback to keyword-based matching
            keyword_match = self._find_keyword_match(
                description, vendor, filtered_categories
            )

            if keyword_match:
                return {
                    "transaction_id": transaction_id,
                    "suggested_category_id": keyword_match["category_id"],
                    "suggested_category_name": keyword_match["category_name"],
                    "confidence_score": keyword_match["confidence"],
                    "reason": keyword_match["reason"],
                    "suggestion_type": "keyword_match"
                }

            return None

        except Exception as e:
            logger.error(f"Failed to suggest category for transaction {transaction.get('id')}: {str(e)}")
            return None

    async def _get_ai_category_suggestion(
        self,
        description: str,
        vendor: str,
        amount: float,
        is_income: bool,
        categories: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Use AI to suggest the most appropriate category.

        Args:
            description: Transaction description
            vendor: Transaction vendor
            amount: Transaction amount
            is_income: Whether it's income
            categories: Available categories

        Returns:
            AI-generated category suggestion
        """
        try:
            # Build category list for AI
            category_list = "\n".join([
                f"- {cat['category_name']}: {cat.get('description', 'No description available')}"
                for cat in categories
            ])

            transaction_type = "income" if is_income else "expense"

            prompt = f"""
You are an expert financial categorizer. Analyze this {transaction_type} transaction and suggest the most appropriate category from the available options.

TRANSACTION DETAILS:
- Description: {description}
- Vendor: {vendor or 'Not specified'}
- Amount: ${amount}
- Type: {transaction_type}

AVAILABLE CATEGORIES (with descriptions):
{category_list}

INSTRUCTIONS:
1. Carefully read each category name and its description
2. Match the transaction to the category whose description best fits the transaction type
3. For example, if a category description mentions "travel" or "hotels", it would be appropriate for hotel stays
4. Consider the business context and common expense patterns
5. Choose the SINGLE most appropriate category from the list above
6. Provide a confidence score from 0.0 to 1.0 based on how well it matches
7. Give a brief reason explaining why the category description fits this transaction

Return ONLY valid JSON in this format:
{{
  "category_name": "Exact category name from list",
  "confidence": 0.85,
  "reason": "Brief explanation of why this category fits based on its description"
}}
"""

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a financial expert specializing in transaction categorization. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": self.temperature,
                "max_tokens": 300
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=15
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            ai_response = json.loads(content)

            suggested_name = ai_response.get("category_name", "").strip()
            confidence = min(1.0, max(0.0, ai_response.get("confidence", 0.5)))
            reason = ai_response.get("reason", "AI analysis")

            # Find matching category
            for category in categories:
                if category["category_name"].lower() == suggested_name.lower():
                    return {
                        "category_id": category["id"],
                        "category_name": category["category_name"],
                        "confidence": confidence,
                        "reason": reason
                    }

            logger.warning(f"AI suggested category '{suggested_name}' not found in available categories")
            return None

        except Exception as e:
            logger.error(f"AI category suggestion failed: {str(e)}")
            return None

    def _find_historical_match(
        self,
        description: str,
        vendor: str,
        amount: float,
        historical_patterns: Dict[str, Any],
        categories: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find category match based on historical patterns.

        Args:
            description: Transaction description
            vendor: Transaction vendor
            amount: Transaction amount
            historical_patterns: Historical categorization data
            categories: Available categories

        Returns:
            Historical pattern match or None
        """
        # Check vendor patterns
        if vendor and vendor in historical_patterns.get("vendor_patterns", {}):
            vendor_data = historical_patterns["vendor_patterns"][vendor]
            category_id = vendor_data.get("category_id")
            confidence = vendor_data.get("confidence", 0.0)

            if category_id and confidence >= 0.7:
                category = next((c for c in categories if c["id"] == category_id), None)
                if category:
                    return {
                        "category_id": category_id,
                        "category_name": category["category_name"],
                        "confidence": confidence,
                        "reason": f"Historical pattern: {vendor} typically categorized as {category['category_name']}"
                    }

        # Check description patterns
        desc_lower = description.lower()
        for pattern, pattern_data in historical_patterns.get("description_patterns", {}).items():
            if pattern.lower() in desc_lower:
                category_id = pattern_data.get("category_id")
                confidence = pattern_data.get("confidence", 0.0)

                if category_id and confidence >= 0.6:
                    category = next((c for c in categories if c["id"] == category_id), None)
                    if category:
                        return {
                            "category_id": category_id,
                            "category_name": category["category_name"],
                            "confidence": confidence,
                            "reason": f"Description pattern match: '{pattern}' typically categorized as {category['category_name']}"
                        }

        return None

    def _find_keyword_match(
        self,
        description: str,
        vendor: str,
        categories: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find category match based on keyword analysis.

        Args:
            description: Transaction description
            vendor: Transaction vendor
            categories: Available categories

        Returns:
            Keyword-based category match
        """
        text_to_analyze = f"{description} {vendor}".lower()

        # Define keyword mappings for common categories
        keyword_mappings = {
            "office": ["office", "supplies", "stationery", "printer", "paper"],
            "travel": ["hotel", "flight", "airline", "taxi", "uber", "lyft", "travel", "mileage"],
            "meals": ["restaurant", "food", "lunch", "dinner", "coffee", "meal", "catering"],
            "software": ["software", "license", "subscription", "saas", "cloud"],
            "utilities": ["electric", "gas", "water", "internet", "phone", "utility"],
            "marketing": ["advertising", "marketing", "social media", "seo", "campaign"],
            "professional services": ["consultant", "legal", "accounting", "audit", "lawyer"],
            "equipment": ["equipment", "hardware", "computer", "laptop", "furniture"],
            "insurance": ["insurance", "premium", "coverage"],
            "training": ["training", "course", "workshop", "seminar", "conference"]
        }

        best_match = None
        best_score = 0

        for category in categories:
            category_name = category["category_name"].lower()
            score = 0

            # Check category name keywords
            for keyword_category, keywords in keyword_mappings.items():
                if keyword_category in category_name:
                    for keyword in keywords:
                        if keyword in text_to_analyze:
                            score += 1
                            break

            # Direct category name match
            if category_name in text_to_analyze:
                score += 2

            # Description match
            category_desc = category.get("description", "").lower()
            if category_desc and any(word in text_to_analyze for word in category_desc.split()):
                score += 1

            if score > best_score and score >= 1:
                best_match = category
                best_score = score

        if best_match:
            confidence = min(0.6, 0.3 + (best_score * 0.1))  # Max 0.6 confidence for keyword matches
            return {
                "category_id": best_match["id"],
                "category_name": best_match["category_name"],
                "confidence": confidence,
                "reason": f"Keyword match based on transaction content"
            }

        return None

    async def _fetch_business_categories(
        self,
        business_id: str,
        supabase_client: Client
    ) -> List[Dict[str, Any]]:
        """
        Fetch categories for the business.

        Args:
            business_id: Business ID
            supabase_client: Supabase client

        Returns:
            List of category dictionaries
        """
        try:
            response = supabase_client.table("categories").select(
                "id, category_name, description, category_type"
            ).eq("business_id", business_id).eq("is_active", True).execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Failed to fetch categories: {str(e)}")
            return []

    async def _get_historical_patterns(
        self,
        business_id: str,
        supabase_client: Client
    ) -> Dict[str, Any]:
        """
        Get historical categorization patterns for the business.

        Args:
            business_id: Business ID
            supabase_client: Supabase client

        Returns:
            Historical pattern data
        """
        try:
            # Get recent transactions with categories to build patterns
            response = supabase_client.table("transactions").select(
                "vendor, description, category_id, amount"
            ).eq("business_id", business_id).not_("category_id", "is", None).execute()

            transactions = response.data or []

            vendor_patterns = {}
            description_patterns = {}

            # Analyze vendor patterns
            vendor_counter = Counter()
            for tx in transactions:
                vendor = tx.get("vendor")
                if vendor:
                    vendor_counter[(vendor, tx["category_id"])] += 1

            # Build vendor patterns
            for (vendor, category_id), count in vendor_counter.items():
                if count >= 2:  # At least 2 transactions for pattern
                    confidence = min(0.9, count / 10)  # Scale confidence
                    vendor_patterns[vendor] = {
                        "category_id": category_id,
                        "confidence": confidence,
                        "transaction_count": count
                    }

            # Analyze description patterns (simplified)
            desc_counter = Counter()
            for tx in transactions:
                desc = tx.get("description", "").lower()
                if desc:
                    # Extract key phrases (simplified approach)
                    words = desc.split()
                    if len(words) >= 2:
                        phrase = " ".join(words[:2])  # First two words
                        desc_counter[(phrase, tx["category_id"])] += 1

            for (phrase, category_id), count in desc_counter.items():
                if count >= 2:
                    confidence = min(0.8, count / 8)
                    description_patterns[phrase] = {
                        "category_id": category_id,
                        "confidence": confidence,
                        "transaction_count": count
                    }

            return {
                "vendor_patterns": vendor_patterns,
                "description_patterns": description_patterns
            }

        except Exception as e:
            logger.error(f"Failed to get historical patterns: {str(e)}")
            return {"vendor_patterns": {}, "description_patterns": {}}

    async def learn_from_correction(
        self,
        transaction_id: str,
        corrected_category_id: str,
        business_id: str,
        supabase_client: Client
    ) -> None:
        """
        Learn from user corrections to improve future suggestions.

        Args:
            transaction_id: Transaction ID that was corrected
            corrected_category_id: The category the user chose
            business_id: Business ID
            supabase_client: Supabase client
        """
        try:
            # Get transaction details
            tx_response = supabase_client.table("transactions").select(
                "vendor, description, amount, is_income"
            ).eq("id", transaction_id).single().execute()

            if not tx_response.data:
                return

            transaction = tx_response.data

            # Store learning data (could be used for future pattern analysis)
            # For now, just log the correction
            logger.info(
                f"Learned from correction: Transaction {transaction_id} "
                f"({transaction.get('description')}) categorized as {corrected_category_id}"
            )

            # TODO: Implement persistent learning storage
            # This could store correction patterns in a dedicated table

        except Exception as e:
            logger.error(f"Failed to learn from correction: {str(e)}")