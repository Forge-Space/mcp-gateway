#!/usr/bin/env node

/**
 * Test script to verify @forgespace/core integration
 */

import { ForgeCore } from '@forgespace/core';

async function testForgeCoreIntegration() {
  console.log('🧪 Testing @forgespace/core integration...');

  try {
    // Test ForgeCore import
    console.log('✅ ForgeCore import successful');

    // Test ForgeCore instantiation
    const forgeCore = new ForgeCore({
      gatewayUrl: 'http://localhost:4444',
      authToken: process.env.FORGE_CORE_TOKEN || 'test-token',
      timeout: 120000,
    });
    console.log('✅ ForgeCore instantiation successful');

    // Test basic configuration
    console.log('✅ Configuration:', {
      gatewayUrl: forgeCore.gatewayUrl,
      timeout: forgeCore.timeout,
      hasAuthToken: !!forgeCore.authToken,
    });

    console.log('🎉 @forgespace/core integration test passed!');
    return true;
  } catch (error) {
    console.error('❌ @forgespace/core integration test failed:', error);
    return false;
  }
}

// Run test if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  testForgeCoreIntegration()
    .then((success) => process.exit(success ? 0 : 1))
    .catch((error) => {
      console.error('Test execution error:', error);
      process.exit(1);
    });
}

export { testForgeCoreIntegration };
