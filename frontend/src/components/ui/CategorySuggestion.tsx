import React, { useState } from 'react';
import { Check, X, Lightbulb, TrendingUp, Brain, Search } from 'lucide-react';
import { CategorySuggestion as CategorySuggestionType } from '../../types';
import Button from './Button';
import { categorySuggestionService } from '../../services/business.service';

interface CategorySuggestionProps {
  suggestion: CategorySuggestionType;
  businessId: string;
  onApplied?: (transactionId: string, categoryId: string) => void;
  onDismissed?: (transactionId: string) => void;
  compact?: boolean;
}

export const CategorySuggestion: React.FC<CategorySuggestionProps> = ({
  suggestion,
  businessId,
  onApplied,
  onDismissed,
  compact = false
}) => {
  const [isApplying, setIsApplying] = useState(false);
  const [isApplied, setIsApplied] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  const getSuggestionIcon = () => {
    switch (suggestion.suggestion_type) {
      case 'historical_pattern':
        return <TrendingUp className="w-4 h-4 text-blue-600" />;
      case 'ai_analysis':
        return <Brain className="w-4 h-4 text-purple-600" />;
      case 'keyword_match':
        return <Search className="w-4 h-4 text-green-600" />;
      default:
        return <Lightbulb className="w-4 h-4 text-yellow-600" />;
    }
  };

  const getConfidenceColor = () => {
    if (suggestion.confidence_score >= 0.8) return 'text-green-700 bg-green-100';
    if (suggestion.confidence_score >= 0.6) return 'text-yellow-700 bg-yellow-100';
    return 'text-orange-700 bg-orange-100';
  };

  const getSuggestionTypeLabel = () => {
    switch (suggestion.suggestion_type) {
      case 'historical_pattern':
        return 'Historical Pattern';
      case 'ai_analysis':
        return 'AI Analysis';
      case 'keyword_match':
        return 'Keyword Match';
      default:
        return 'Suggestion';
    }
  };

  const handleApply = async () => {
    setIsApplying(true);
    try {
      await categorySuggestionService.applySuggestion(
        suggestion.transaction_id,
        suggestion.suggested_category_id,
        businessId
      );
      setIsApplied(true);
      onApplied?.(suggestion.transaction_id, suggestion.suggested_category_id);
    } catch (error) {
      console.error('Failed to apply category suggestion:', error);
      alert('Failed to apply category suggestion. Please try again.');
    } finally {
      setIsApplying(false);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismissed?.(suggestion.transaction_id);
  };

  if (isApplied || isDismissed) {
    return null;
  }

  if (compact) {
    return (
      <div className="flex items-center gap-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
        {getSuggestionIcon()}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-blue-900 truncate">
            {suggestion.suggested_category_name}
          </p>
          <p className="text-xs text-blue-700">
            {Math.round(suggestion.confidence_score * 100)}% confidence
          </p>
        </div>
        <div className="flex gap-1">
          <Button
            size="sm"
            variant="ghost"
            onClick={handleApply}
            disabled={isApplying}
            className="h-6 w-6 p-0 text-green-600 hover:bg-green-100"
          >
            <Check className="w-3 h-3" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleDismiss}
            className="h-6 w-6 p-0 text-gray-600 hover:bg-gray-100"
          >
            <X className="w-3 h-3" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          {getSuggestionIcon()}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <h4 className="text-sm font-semibold text-blue-900">
              Suggested Category
            </h4>
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor()}`}>
              {Math.round(suggestion.confidence_score * 100)}% confidence
            </span>
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
              {getSuggestionTypeLabel()}
            </span>
          </div>

          <p className="text-lg font-bold text-blue-900 mb-2">
            {suggestion.suggested_category_name}
          </p>

          <p className="text-sm text-blue-800 mb-3">
            {suggestion.reason}
          </p>

          <div className="flex gap-2">
            <Button
              size="sm"
              variant="primary"
              onClick={handleApply}
              disabled={isApplying}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isApplying ? (
                <>
                  <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin mr-1"></div>
                  Applying...
                </>
              ) : (
                <>
                  <Check className="w-3 h-3 mr-1" />
                  Apply Category
                </>
              )}
            </Button>

            <Button
              size="sm"
              variant="ghost"
              onClick={handleDismiss}
              className="text-gray-600 hover:bg-gray-100"
            >
              <X className="w-3 h-3 mr-1" />
              Dismiss
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};