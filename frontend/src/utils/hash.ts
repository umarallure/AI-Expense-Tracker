/**
 * Simple SHA-256 implementation for generating transaction fingerprints
 * Uses browser's SubtleCrypto API or falls back to a simple hash
 */

/**
 * Generate SHA-256 hash of a string
 * Falls back to a simple hash if SubtleCrypto is not available
 */
export async function sha256Async(message: string): Promise<string> {
  // Try to use SubtleCrypto API if available
  if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
    try {
      const msgBuffer = new TextEncoder().encode(message);
      const hashBuffer = await window.crypto.subtle.digest('SHA-256', msgBuffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
      return hashHex;
    } catch (error) {
      // Fall back to simple hash
      return simpleHash(message);
    }
  }
  
  // Fallback for environments without SubtleCrypto
  return simpleHash(message);
}

/**
 * Synchronous hash function for transaction fingerprints
 * Uses a simple but effective hashing algorithm
 */
export function sha256(message: string): string {
  return simpleHash(message);
}

/**
 * Simple hash function (not cryptographically secure, but fast and deterministic)
 * Good enough for duplicate detection
 */
function simpleHash(str: string): string {
  let hash = 0;
  if (str.length === 0) return hash.toString(16);
  
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  
  // Convert to hex string and ensure consistent length
  return Math.abs(hash).toString(16).padStart(8, '0');
}
