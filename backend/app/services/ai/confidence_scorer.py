"""
Confidence Scorer Service
Calculates overall extraction confidence from field-level scores.
"""
from typing import Dict, Any
from loguru import logger


class ConfidenceScorer:
    """
    Calculate confidence scores for extracted data.
    
    Determines:
    - Overall extraction confidence
    - Auto-approval eligibility (threshold: 0.85)
    - Field-level confidence aggregation
    """
    
    # Confidence thresholds
    AUTO_APPROVAL_THRESHOLD = 0.85
    MANUAL_REVIEW_THRESHOLD = 0.60
    
    # Field importance weights (higher = more critical)
    FIELD_WEIGHTS = {
        "vendor": 0.20,
        "amount": 0.30,      # Most critical field
        "date": 0.20,
        "description": 0.10,
        "category": 0.10,
        "payment_method": 0.05,
        "recipient_id": 0.05
    }
    
    def __init__(self):
        """Initialize ConfidenceScorer"""
        pass
    
    def calculate_overall_confidence(
        self,
        field_confidence: Dict[str, float],
        extracted_fields: Dict[str, Any]
    ) -> float:
        """
        Calculate overall extraction confidence from field-level scores.
        
        Args:
            field_confidence: Dictionary of field_name -> confidence_score
            extracted_fields: Dictionary of extracted field values
            
        Returns:
            Overall confidence score (0.0 to 1.0)
            
        Example:
            >>> scorer = ConfidenceScorer()
            >>> field_conf = {"vendor": 0.95, "amount": 0.99, "date": 0.90}
            >>> fields = {"vendor": "Acme Corp", "amount": 150.00, "date": "2023-01-15"}
            >>> overall = scorer.calculate_overall_confidence(field_conf, fields)
            >>> print(f"Overall confidence: {overall:.2f}")
            Overall confidence: 0.94
        """
        try:
            if not field_confidence:
                return 0.0
            
            # Calculate weighted average of field confidences
            total_weight = 0.0
            weighted_sum = 0.0
            
            for field, confidence in field_confidence.items():
                # Get weight for this field (default to 0.05 for unknown fields)
                weight = self.FIELD_WEIGHTS.get(field, 0.05)
                
                # Only include if field has a value
                if extracted_fields.get(field) is not None:
                    weighted_sum += confidence * weight
                    total_weight += weight
            
            # Calculate overall confidence
            if total_weight > 0:
                overall_confidence = weighted_sum / total_weight
            else:
                overall_confidence = 0.0
            
            # Apply penalties for missing critical fields
            overall_confidence = self._apply_missing_field_penalty(
                overall_confidence,
                extracted_fields
            )
            
            # Ensure confidence is between 0 and 1
            overall_confidence = max(0.0, min(1.0, overall_confidence))
            
            logger.debug(
                f"Calculated overall confidence: {overall_confidence:.3f} "
                f"(weighted_sum: {weighted_sum:.3f}, total_weight: {total_weight:.3f})"
            )
            
            return overall_confidence
            
        except Exception as e:
            logger.error(f"Failed to calculate overall confidence: {str(e)}")
            return 0.0
    
    def _apply_missing_field_penalty(
        self,
        confidence: float,
        extracted_fields: Dict[str, Any]
    ) -> float:
        """
        Apply penalty for missing critical fields.
        
        Args:
            confidence: Current confidence score
            extracted_fields: Extracted field values
            
        Returns:
            Adjusted confidence score
        """
        # Critical fields that should always be present
        critical_fields = ["vendor", "amount", "date"]
        
        missing_critical = []
        for field in critical_fields:
            value = extracted_fields.get(field)
            if value is None or value == "" or value == 0:
                missing_critical.append(field)
        
        # Apply penalty: -0.15 for each missing critical field
        penalty = len(missing_critical) * 0.15
        adjusted_confidence = confidence - penalty
        
        if missing_critical:
            logger.warning(
                f"Missing critical fields: {missing_critical}. "
                f"Applied penalty: -{penalty:.2f}"
            )
        
        return max(0.0, adjusted_confidence)
    
    def should_auto_approve(self, overall_confidence: float) -> bool:
        """
        Determine if extraction should be auto-approved.
        
        Args:
            overall_confidence: Overall confidence score
            
        Returns:
            True if confidence >= AUTO_APPROVAL_THRESHOLD
        """
        return overall_confidence >= self.AUTO_APPROVAL_THRESHOLD
    
    def requires_manual_review(self, overall_confidence: float) -> bool:
        """
        Determine if extraction requires manual review.
        
        Args:
            overall_confidence: Overall confidence score
            
        Returns:
            True if confidence < MANUAL_REVIEW_THRESHOLD
        """
        return overall_confidence < self.MANUAL_REVIEW_THRESHOLD
    
    def get_confidence_level(self, overall_confidence: float) -> str:
        """
        Get human-readable confidence level.
        
        Args:
            overall_confidence: Overall confidence score
            
        Returns:
            Confidence level: "high", "medium", or "low"
        """
        if overall_confidence >= self.AUTO_APPROVAL_THRESHOLD:
            return "high"
        elif overall_confidence >= self.MANUAL_REVIEW_THRESHOLD:
            return "medium"
        else:
            return "low"
    
    def get_recommendation(self, overall_confidence: float) -> Dict[str, Any]:
        """
        Get recommendation for handling the extraction.
        
        Args:
            overall_confidence: Overall confidence score
            
        Returns:
            Dictionary with recommendation details
        """
        confidence_level = self.get_confidence_level(overall_confidence)
        auto_approve = self.should_auto_approve(overall_confidence)
        requires_review = self.requires_manual_review(overall_confidence)
        
        if auto_approve:
            action = "auto_approve"
            message = "High confidence - transaction can be auto-created"
        elif requires_review:
            action = "manual_review_required"
            message = "Low confidence - manual review required before creating transaction"
        else:
            action = "review_recommended"
            message = "Medium confidence - review recommended but optional"
        
        return {
            "action": action,
            "message": message,
            "confidence_level": confidence_level,
            "auto_approve": auto_approve,
            "requires_review": requires_review,
            "overall_confidence": overall_confidence
        }
    
    def aggregate_field_confidence(
        self,
        field_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Aggregate field-level confidence scores.
        
        Args:
            field_scores: Dictionary of field -> confidence
            
        Returns:
            Aggregated statistics
        """
        if not field_scores:
            return {
                "average": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0
            }
        
        scores = list(field_scores.values())
        return {
            "average": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores),
            "count": len(scores),
            "high_confidence_fields": [
                field for field, score in field_scores.items()
                if score >= 0.90
            ],
            "low_confidence_fields": [
                field for field, score in field_scores.items()
                if score < 0.70
            ]
        }
