import React from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { DuplicateMatch } from '../../utils/duplicateDetection';
import type { Category, Account } from '../../types';

interface DuplicateWarningProps {
  duplicates: DuplicateMatch[];
  categories: Category[];
  accounts: Account[];
  onDismiss: () => void;
  onViewDuplicate?: (transactionId: string) => void;
}

const DuplicateWarning: React.FC<DuplicateWarningProps> = ({
  duplicates,
  categories,
  accounts,
  onDismiss,
  onViewDuplicate
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const getMatchScoreColor = (score: number) => {
    if (score >= 0.95) return 'text-red-700';
    if (score >= 0.85) return 'text-orange-700';
    return 'text-yellow-700';
  };

  const getMatchScoreBg = (score: number) => {
    if (score >= 0.95) return 'bg-red-50 border-red-200';
    if (score >= 0.85) return 'bg-orange-50 border-orange-200';
    return 'bg-yellow-50 border-yellow-200';
  };

  return (
    <div className={`border rounded-lg p-4 ${getMatchScoreBg(duplicates[0]?.matchScore || 0)}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className={`w-5 h-5 ${getMatchScoreColor(duplicates[0]?.matchScore || 0)}`} />
          <div>
            <h4 className="font-semibold text-gray-900">
              {duplicates.length === 1 ? 'Potential Duplicate Detected' : `${duplicates.length} Potential Duplicates Detected`}
            </h4>
            <p className="text-sm text-gray-600 mt-0.5">
              This transaction appears similar to existing transaction(s). Please review before submitting.
            </p>
          </div>
        </div>
        <button
          onClick={onDismiss}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Dismiss warning"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="space-y-3 mt-4">
        {duplicates.slice(0, 3).map((duplicate) => {
          const transaction = duplicate.transaction;
          const matchPercentage = Math.round(duplicate.matchScore * 100);
          
          return (
            <div
              key={transaction.id}
              className="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getMatchScoreBg(duplicate.matchScore)}`}>
                      {matchPercentage}% Match
                    </span>
                    <span className="text-xs text-gray-500">
                      {duplicate.matchReasons.join(' • ')}
                    </span>
                  </div>
                  <p className="font-medium text-gray-900">{transaction.description}</p>
                </div>
                {onViewDuplicate && (
                  <button
                    onClick={() => onViewDuplicate(transaction.id)}
                    className="text-primary-600 hover:text-primary-700 text-sm font-medium ml-2"
                  >
                    View
                  </button>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-gray-600">
                <div>
                  <span className="text-gray-500">Date:</span>{' '}
                  {formatDate(transaction.date)}
                </div>
                <div>
                  <span className="text-gray-500">Amount:</span>{' '}
                  {formatCurrency(transaction.amount, transaction.currency)}
                </div>
                {transaction.vendor && (
                  <div>
                    <span className="text-gray-500">Vendor:</span>{' '}
                    {transaction.vendor}
                  </div>
                )}
                <div>
                  <span className="text-gray-500">Category:</span>{' '}
                  {categories.find(cat => cat.id === transaction.category_id)?.category_name || 'Unknown'}
                </div>
                <div>
                  <span className="text-gray-500">Account:</span>{' '}
                  {accounts.find(acc => acc.id === transaction.account_id)?.account_name || 'Unknown'}
                </div>
                <div>
                  <span className="text-gray-500">Status:</span>{' '}
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    transaction.status === 'approved' ? 'bg-green-100 text-green-700' :
                    transaction.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                    transaction.status === 'rejected' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
        
        {duplicates.length > 3 && (
          <p className="text-sm text-gray-600 text-center py-2">
            ... and {duplicates.length - 3} more potential duplicate(s)
          </p>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-gray-300">
        <p className="text-xs text-gray-600">
          <strong>Note:</strong> If this is not a duplicate, you can proceed with creating the transaction.
          The system uses date, amount, vendor, and description to detect potential duplicates.
        </p>
      </div>
    </div>
  );
};

export default DuplicateWarning;
