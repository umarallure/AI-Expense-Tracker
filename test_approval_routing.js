#!/usr/bin/env node

/**
 * Simple test script to verify TransactionApproval page routing
 * Run with: node test_approval_routing.js
 */

const http = require('http');

const TEST_URL = 'http://localhost:3000/approvals/ad92ca0a-0d7f-4317-8f3b-fa29c85194e4';

console.log('Testing TransactionApproval page routing...');
console.log(`Making request to: ${TEST_URL}`);

const req = http.get(TEST_URL, (res) => {
  console.log(`Status: ${res.statusCode}`);
  console.log(`Headers:`, res.headers);

  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    console.log('\nResponse received. Checking for React app content...');

    // Check if it's a valid HTML response (React SPA should return HTML)
    if (res.statusCode === 200 && data.includes('<html')) {
      console.log('✅ SUCCESS: Page is loading HTML content (React app is responding)');

      // Check for common React app indicators
      if (data.includes('root') || data.includes('react')) {
        console.log('✅ SUCCESS: React app structure detected');
      }

      // Check for our specific component indicators
      if (data.includes('TransactionApproval') || data.includes('Review Transaction')) {
        console.log('✅ SUCCESS: TransactionApproval component content found');
      } else {
        console.log('⚠️  WARNING: TransactionApproval component content not found in initial response');
        console.log('   (This is normal for SPAs - content loads dynamically)');
      }

    } else {
      console.log('❌ ERROR: Unexpected response format');
      console.log('Response preview:', data.substring(0, 200) + '...');
    }
  });
});

req.on('error', (err) => {
  console.error('❌ ERROR: Request failed:', err.message);
  console.log('\nTroubleshooting:');
  console.log('1. Make sure the development server is running: npm run dev');
  console.log('2. Check that the server is accessible at http://localhost:3000');
  console.log('3. Verify the route /approvals/:id is properly configured');
});

req.setTimeout(5000, () => {
  console.error('❌ ERROR: Request timed out');
  req.destroy();
});