/**
 * Test script for duplicate detection functionality
 * Run this to verify the duplicate detection algorithms work correctly
 */

import { detectDuplicates, findExactDuplicates, isExactDuplicate } from './duplicateDetection';
import type { Expense } from '../types';

// Mock test data
const mockTransactions: Expense[] = [
  {
    id: '1',
    business_id: 'biz-1',
    account_id: 'acc-1',
    category_id: 'cat-1',
    user_id: 'user-1',
    amount: 150.00,
    currency: 'USD',
    description: 'Hotel stay for 1 night',
    date: '2025-10-20T10:00:00Z',
    is_income: false,
    status: 'approved',
    vendor: 'Marriott Hotels',
    created_at: '2025-10-20T10:00:00Z',
    updated_at: '2025-10-20T10:00:00Z',
  },
  {
    id: '2',
    business_id: 'biz-1',
    account_id: 'acc-1',
    category_id: 'cat-1',
    user_id: 'user-1',
    amount: 150.00,
    currency: 'USD',
    description: 'Hotel stay for 1 night',
    date: '2025-10-20T10:00:00Z',
    is_income: false,
    status: 'approved',
    vendor: 'Marriott Hotels',
    created_at: '2025-10-20T10:00:00Z',
    updated_at: '2025-10-20T10:00:00Z',
  },
  {
    id: '3',
    business_id: 'biz-1',
    account_id: 'acc-1',
    category_id: 'cat-1',
    user_id: 'user-1',
    amount: 150.00,
    currency: 'USD',
    description: 'Hotel stay for 1 night',
    date: '2025-10-22T10:00:00Z', // 2 days later
    is_income: false,
    status: 'pending',
    vendor: 'Marriott Hotels',
    created_at: '2025-10-22T10:00:00Z',
    updated_at: '2025-10-22T10:00:00Z',
  },
  {
    id: '4',
    business_id: 'biz-1',
    account_id: 'acc-2',
    category_id: 'cat-2',
    user_id: 'user-1',
    amount: 89.99,
    currency: 'USD',
    description: 'Office supplies from Amazon',
    date: '2025-10-15T10:00:00Z',
    is_income: false,
    status: 'approved',
    vendor: 'Amazon',
    created_at: '2025-10-15T10:00:00Z',
    updated_at: '2025-10-15T10:00:00Z',
  },
  {
    id: '5',
    business_id: 'biz-1',
    account_id: 'acc-2',
    category_id: 'cat-2',
    user_id: 'user-1',
    amount: 89.99,
    currency: 'USD',
    description: 'Office supplies from Amazon',
    date: '2025-10-15T10:00:00Z',
    is_income: false,
    status: 'approved',
    vendor: 'Amazon',
    created_at: '2025-10-15T10:00:00Z',
    updated_at: '2025-10-15T10:00:00Z',
  },
];

// Test functions
export function runDuplicateDetectionTests() {
  console.log('🧪 Running Duplicate Detection Tests...\n');

  // Test 1: Find exact duplicates
  console.log('1. Testing findExactDuplicates...');
  const exactDuplicates = findExactDuplicates(mockTransactions);
  console.log(`Found ${exactDuplicates.size} duplicate groups:`);
  for (const [fingerprint, group] of exactDuplicates.entries()) {
    console.log(`  Group (${group.length} items): ${group.map(t => t.id).join(', ')}`);
    console.log(`  Sample: "${group[0].description}" - $${group[0].amount} - ${group[0].vendor}`);
  }
  console.log('');

  // Test 2: Detect duplicates for new transaction (exact match)
  console.log('2. Testing detectDuplicates (exact match)...');
  const newTransaction = {
    date: '2025-10-20',
    amount: 150.00,
    vendor: 'Marriott Hotels',
    description: 'Hotel stay for 1 night',
  };

  const result = detectDuplicates(newTransaction, mockTransactions, {
    fuzzyMatchThreshold: 0.85,
    dateTolerance: 2,
  });

  console.log(`Is duplicate: ${result.isDuplicate}`);
  console.log(`Number of matches: ${result.duplicates.length}`);
  result.duplicates.forEach((match, index) => {
    console.log(`  Match ${index + 1}: ${Math.round(match.matchScore * 100)}% - ${match.matchReasons.join(', ')}`);
  });
  console.log('');

  // Test 3: Detect duplicates for new transaction (similar but not exact)
  console.log('3. Testing detectDuplicates (similar transaction)...');
  const similarTransaction = {
    date: '2025-10-21', // 1 day later
    amount: 150.00,
    vendor: 'Marriott Hotels',
    description: 'Hotel stay for 1 night',
  };

  const similarResult = detectDuplicates(similarTransaction, mockTransactions, {
    fuzzyMatchThreshold: 0.85,
    dateTolerance: 2,
  });

  console.log(`Is duplicate: ${similarResult.isDuplicate}`);
  console.log(`Number of matches: ${similarResult.duplicates.length}`);
  similarResult.duplicates.forEach((match, index) => {
    console.log(`  Match ${index + 1}: ${Math.round(match.matchScore * 100)}% - ${match.matchReasons.join(', ')}`);
  });
  console.log('');

  // Test 4: Detect duplicates for non-duplicate transaction
  console.log('4. Testing detectDuplicates (non-duplicate)...');
  const nonDuplicateTransaction = {
    date: '2025-10-25',
    amount: 50.00,
    vendor: 'Starbucks',
    description: 'Coffee and pastries',
  };

  const nonDuplicateResult = detectDuplicates(nonDuplicateTransaction, mockTransactions, {
    fuzzyMatchThreshold: 0.85,
    dateTolerance: 2,
  });

  console.log(`Is duplicate: ${nonDuplicateResult.isDuplicate}`);
  console.log(`Number of matches: ${nonDuplicateResult.duplicates.length}`);
  console.log('');

  // Test 5: Test isExactDuplicate
  console.log('5. Testing isExactDuplicate...');
  const exactMatch = isExactDuplicate(newTransaction, mockTransactions);
  console.log(`Exact duplicate check: ${exactMatch}`);

  const nonExactMatch = isExactDuplicate(nonDuplicateTransaction, mockTransactions);
  console.log(`Non-exact duplicate check: ${nonExactMatch}`);

  console.log('\n✅ All tests completed!');
}

// Auto-run tests in development
if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
  // Uncomment to run tests automatically
  // runDuplicateDetectionTests();
}

export { mockTransactions };