import { Expense } from '../types';
import { sha256 } from './hash';

/**
 * Duplicate detection utility for transactions
 * Uses hash-based matching considering date, amount, vendor, and description
 */

export interface DuplicateMatch {
  transaction: Expense;
  matchScore: number;
  matchReasons: string[];
}

export interface DuplicateDetectionResult {
  isDuplicate: boolean;
  duplicates: DuplicateMatch[];
}

/**
 * Generate a transaction fingerprint for exact duplicate detection
 * Uses date, amount, vendor, and description
 */
export function generateTransactionFingerprint(transaction: {
  date: string;
  amount: number;
  vendor?: string;
  description: string;
}): string {
  const normalizedDate = new Date(transaction.date).toISOString().split('T')[0];
  const normalizedAmount = transaction.amount.toFixed(2);
  const normalizedVendor = (transaction.vendor || '').toLowerCase().trim();
  const normalizedDescription = transaction.description.toLowerCase().trim();
  
  const fingerprint = `${normalizedDate}|${normalizedAmount}|${normalizedVendor}|${normalizedDescription}`;
  return sha256(fingerprint);
}

/**
 * Normalize a string for comparison (lowercase, remove extra spaces)
 */
function normalizeString(str: string): string {
  return str.toLowerCase().trim().replace(/\s+/g, ' ');
}

/**
 * Calculate similarity score between two strings (0-1)
 * Uses Levenshtein distance-based algorithm
 */
function calculateStringSimilarity(str1: string, str2: string): number {
  const s1 = normalizeString(str1);
  const s2 = normalizeString(str2);
  
  if (s1 === s2) return 1;
  if (s1.length === 0 || s2.length === 0) return 0;
  
  // Simple substring matching as a fast approximation
  if (s1.includes(s2) || s2.includes(s1)) {
    return Math.max(s2.length / s1.length, s1.length / s2.length);
  }
  
  // Levenshtein distance
  const matrix: number[][] = [];
  
  for (let i = 0; i <= s1.length; i++) {
    matrix[i] = [i];
  }
  
  for (let j = 0; j <= s2.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= s1.length; i++) {
    for (let j = 1; j <= s2.length; j++) {
      if (s1[i - 1] === s2[j - 1]) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1, // substitution
          matrix[i][j - 1] + 1,     // insertion
          matrix[i - 1][j] + 1      // deletion
        );
      }
    }
  }
  
  const maxLength = Math.max(s1.length, s2.length);
  const distance = matrix[s1.length][s2.length];
  return 1 - distance / maxLength;
}

/**
 * Check if two amounts are approximately equal (within 0.5%)
 */
function areAmountsEqual(amount1: number, amount2: number): boolean {
  if (amount1 === amount2) return true;
  const diff = Math.abs(amount1 - amount2);
  const avg = (amount1 + amount2) / 2;
  return diff / avg < 0.005; // 0.5% tolerance
}

/**
 * Detect potential duplicates for a new transaction
 * Returns transactions that might be duplicates with match scores
 */
export function detectDuplicates(
  newTransaction: {
    date: string;
    amount: number;
    vendor?: string;
    description: string;
  },
  existingTransactions: Expense[],
  options: {
    fuzzyMatchThreshold?: number;
    dateTolerance?: number; // days
  } = {}
): DuplicateDetectionResult {
  const {
    fuzzyMatchThreshold = 0.85,   // 85% similarity
    dateTolerance = 0             // Same day only
  } = options;
  
  const duplicates: DuplicateMatch[] = [];
  const newDate = new Date(newTransaction.date);
  
  for (const existing of existingTransactions) {
    const matchReasons: string[] = [];
    let matchScore = 0;
    let weights = 0;
    
    // Date matching (weight: 30%)
    const existingDate = new Date(existing.date);
    const daysDiff = Math.abs((newDate.getTime() - existingDate.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysDiff <= dateTolerance) {
      matchScore += 30;
      weights += 30;
      if (daysDiff === 0) {
        matchReasons.push('Same date');
      } else {
        matchReasons.push(`Within ${daysDiff} day(s)`);
      }
    } else {
      weights += 30;
    }
    
    // Amount matching (weight: 35%)
    if (areAmountsEqual(newTransaction.amount, existing.amount)) {
      matchScore += 35;
      weights += 35;
      matchReasons.push('Same amount');
    } else {
      weights += 35;
    }
    
    // Vendor matching (weight: 15%)
    if (newTransaction.vendor && existing.vendor) {
      const vendorSimilarity = calculateStringSimilarity(
        newTransaction.vendor,
        existing.vendor
      );
      if (vendorSimilarity > 0.8) {
        matchScore += 15 * vendorSimilarity;
        weights += 15;
        if (vendorSimilarity === 1) {
          matchReasons.push('Identical vendor');
        } else {
          matchReasons.push('Similar vendor');
        }
      } else {
        weights += 15;
      }
    }
    
    // Description matching (weight: 20%)
    const descSimilarity = calculateStringSimilarity(
      newTransaction.description,
      existing.description
    );
    if (descSimilarity > 0.7) {
      matchScore += 20 * descSimilarity;
      weights += 20;
      if (descSimilarity === 1) {
        matchReasons.push('Identical description');
      } else {
        matchReasons.push('Similar description');
      }
    } else {
      weights += 20;
    }
    
    // Calculate final score (0-1)
    const finalScore = weights > 0 ? matchScore / weights : 0;
    
    // Check if this is a potential duplicate
    if (finalScore >= fuzzyMatchThreshold) {
      duplicates.push({
        transaction: existing,
        matchScore: finalScore,
        matchReasons
      });
    }
  }
  
  // Sort by match score (highest first)
  duplicates.sort((a, b) => b.matchScore - a.matchScore);
  
  return {
    isDuplicate: duplicates.length > 0,
    duplicates
  };
}

/**
 * Find exact duplicates in a list of transactions
 * Returns groups of transactions that are exact duplicates
 */
export function findExactDuplicates(transactions: Expense[]): Map<string, Expense[]> {
  const fingerprintMap = new Map<string, Expense[]>();
  
  for (const transaction of transactions) {
    const fingerprint = generateTransactionFingerprint({
      date: transaction.date,
      amount: transaction.amount,
      vendor: transaction.vendor,
      description: transaction.description
    });
    
    if (!fingerprintMap.has(fingerprint)) {
      fingerprintMap.set(fingerprint, []);
    }
    fingerprintMap.get(fingerprint)!.push(transaction);
  }
  
  // Filter to only include groups with duplicates
  const duplicateGroups = new Map<string, Expense[]>();
  for (const [fingerprint, group] of fingerprintMap.entries()) {
    if (group.length > 1) {
      duplicateGroups.set(fingerprint, group);
    }
  }
  
  return duplicateGroups;
}

/**
 * Check if a transaction is an exact duplicate of any existing transaction
 */
export function isExactDuplicate(
  newTransaction: {
    date: string;
    amount: number;
    vendor?: string;
    description: string;
  },
  existingTransactions: Expense[]
): boolean {
  const newFingerprint = generateTransactionFingerprint(newTransaction);
  
  for (const existing of existingTransactions) {
    const existingFingerprint = generateTransactionFingerprint({
      date: existing.date,
      amount: existing.amount,
      vendor: existing.vendor,
      description: existing.description
    });
    
    if (newFingerprint === existingFingerprint) {
      return true;
    }
  }
  
  return false;
}
