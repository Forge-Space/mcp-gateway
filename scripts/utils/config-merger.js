#!/usr/bin/env node

/**
 * Configuration Merger Utility
 *
 * This utility helps merge forge-patterns base configurations
 * with project-specific customizations for forge-mcp-gateway.
 *
 * Usage: node scripts/utils/config-merger.js [options]
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class ConfigMerger {
  constructor() {
    this.projectRoot = path.resolve(__dirname, '../..');
    this.patternsPath = path.resolve(this.projectRoot, '../forge-patterns');
  }

  /**
   * Load and parse a JSON configuration file
   */
  loadJsonConfig(filePath) {
    try {
      const fullPath = path.resolve(filePath);
      if (!fs.existsSync(fullPath)) {
        console.warn(`⚠️  Config file not found: ${fullPath}`);
        return {};
      }
      const content = fs.readFileSync(fullPath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      console.error(`❌ Error loading config ${filePath}:`, error.message);
      return {};
    }
  }

  /**
   * Load and parse a JavaScript configuration file
   */
  loadJsConfig(filePath) {
    try {
      const fullPath = path.resolve(filePath);
      if (!fs.existsSync(fullPath)) {
        console.warn(`⚠️  Config file not found: ${fullPath}`);
        return {};
      }

      // Read the file content
      const content = fs.readFileSync(fullPath, 'utf8');

      // For ESLint flat config with import.meta
      if (content.includes('import.meta')) {
        // Extract the configuration by removing import.meta usage
        const processedContent = content
          .replace(/import\.meta\.dirname/g, `'${path.dirname(fullPath)}'`)
          .replace(/import\s+.*?from/g, '// import removed')
          .replace(/export default\s+/, 'module.exports = ');

        const tempFile = fullPath + '.temp.cjs';
        fs.writeFileSync(tempFile, processedContent);

        try {
          // Remove the module from require cache to ensure fresh load
          delete require.cache[require.resolve(tempFile)];
          const module = require(tempFile);
          return module || {};
        } finally {
          // Clean up temp file
          if (fs.existsSync(tempFile)) {
            fs.unlinkSync(tempFile);
          }
        }
      }

      // For CommonJS modules (like forge-patterns)
      if (content.includes('module.exports')) {
        const tempFile = fullPath + '.temp.cjs';
        fs.writeFileSync(tempFile, content);

        try {
          delete require.cache[require.resolve(tempFile)];
          const module = require(tempFile);
          return module || {};
        } finally {
          if (fs.existsSync(tempFile)) {
            fs.unlinkSync(tempFile);
          }
        }
      }

      // For ES modules with export default
      if (content.includes('export default')) {
        const moduleContent = content.replace(/export default/g, 'module.exports = ');
        const tempFile = fullPath + '.temp.cjs';
        fs.writeFileSync(tempFile, moduleContent);

        try {
          delete require.cache[require.resolve(tempFile)];
          const module = require(tempFile);
          return module || {};
        } finally {
          if (fs.existsSync(tempFile)) {
            fs.unlinkSync(tempFile);
          }
        }
      }

      console.warn(`⚠️  Unable to parse config file: ${fullPath}`);
      return {};

    } catch (error) {
      console.error(`❌ Error loading config ${filePath}:`, error.message);
      return {};
    }
  }

  /**
   * Deep merge two objects
   */
  deepMerge(target, source) {
    const result = { ...target };

    for (const key in source) {
      if (source.hasOwnProperty(key)) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
          result[key] = this.deepMerge(result[key] || {}, source[key]);
        } else {
          result[key] = source[key];
        }
      }
    }

    return result;
  }

  /**
   * Merge ESLint configurations
   */
  mergeEslintConfig() {
    console.log('🔧 Merging ESLint configurations...');

    // Load current ESLint config
    const currentConfig = this.loadJsConfig('./eslint.config.js');

    // Load base patterns ESLint config
    const basePatternsPath = path.join(this.patternsPath, 'patterns/code-quality/eslint/base.config.js');
    const baseConfig = this.loadJsConfig(basePatternsPath);

    // Create merged configuration
    const mergedConfig = {
      ...currentConfig,
      // Add pattern reference comment
      _patternInfo: {
        baseConfig: 'forge-patterns/patterns/code-quality/eslint/base.config.js',
        mergedAt: new Date().toISOString(),
        project: 'forge-mcp-gateway'
      }
    };

    return mergedConfig;
  }

  /**
   * Merge Prettier configurations
   */
  mergePrettierConfig() {
    console.log('🎨 Merging Prettier configurations...');

    // Load current Prettier config
    const currentConfig = this.loadJsonConfig('./.prettierrc.json');

    // Load base patterns Prettier config
    const basePatternsPath = path.join(this.patternsPath, 'patterns/code-quality/prettier/base.config.json');
    const baseConfig = this.loadJsonConfig(basePatternsPath);

    // Create merged configuration with project-specific overrides
    const mergedConfig = {
      ...baseConfig,
      // Preserve project-specific settings
      trailingComma: currentConfig.trailingComma || "none",
      arrowParens: currentConfig.arrowParens || "avoid",
      // Merge overrides
      overrides: [
        ...(baseConfig.overrides || []),
        ...(currentConfig.overrides || [])
      ],
      // Add pattern reference
      _patternInfo: {
        baseConfig: 'forge-patterns/patterns/code-quality/prettier/base.config.json',
        mergedAt: new Date().toISOString(),
        project: 'forge-mcp-gateway'
      }
    };

    return mergedConfig;
  }

  /**
   * Validate merged configuration
   */
  validateConfig(config, type) {
    console.log(`✅ Validating ${type} configuration...`);

    const issues = [];

    if (type === 'eslint') {
      // ESLint specific validations
      if (!config.root && config.root !== false) {
        issues.push('Missing root property');
      }
      if (!config.extends || !Array.isArray(config.extends)) {
        issues.push('Invalid or missing extends property');
      }
    } else if (type === 'prettier') {
      // Prettier specific validations
      if (typeof config.semi !== 'boolean') {
        issues.push('Invalid semi property');
      }
      if (typeof config.singleQuote !== 'boolean') {
        issues.push('Invalid singleQuote property');
      }
    }

    if (issues.length > 0) {
      console.warn(`⚠️  ${type} validation issues:`);
      issues.forEach(issue => console.warn(`  - ${issue}`));
      return false;
    }

    console.log(`✅ ${type} configuration validation passed`);
    return true;
  }

  /**
   * Backup current configuration
   */
  backupConfig(filePath) {
    const backupPath = `${filePath}.backup.${Date.now()}`;
    try {
      fs.copyFileSync(filePath, backupPath);
      console.log(`💾 Backed up ${filePath} to ${backupPath}`);
      return backupPath;
    } catch (error) {
      console.error(`❌ Error backing up ${filePath}:`, error.message);
      return null;
    }
  }

  /**
   * Write merged configuration
   */
  writeConfig(config, filePath, type) {
    try {
      let content;

      if (type === 'eslint') {
        // Generate ESLint config file content
        content = this.generateEslintConfig(config);
      } else if (type === 'prettier') {
        // Generate Prettier config file content
        content = JSON.stringify(config, null, 2) + '\n';
      }

      fs.writeFileSync(filePath, content);
      console.log(`✅ Wrote merged ${type} configuration to ${filePath}`);
      return true;
    } catch (error) {
      console.error(`❌ Error writing ${type} configuration:`, error.message);
      return false;
    }
  }

  /**
   * Generate ESLint configuration file content
   */
  generateEslintConfig(config) {
    const { _patternInfo, ...eslintConfig } = config;

    return `// ESLint Configuration for forge-mcp-gateway
// Merged with forge-patterns base configuration
// Base: ${_patternInfo.baseConfig}
// Merged: ${_patternInfo.mergedAt}

import js from '@eslint/js';
import importPlugin from 'eslint-plugin-import';
import typescriptEslint from 'typescript-eslint';

export default ${JSON.stringify(eslintConfig, null, 2)};
`;
  }

  /**
   * Run the complete merge process
   */
  run(options = {}) {
    console.log('🚀 Starting configuration merge process...\n');

    const results = {
      eslint: { success: false, backup: null },
      prettier: { success: false, backup: null }
    };

    // Process ESLint configuration
    if (!options.skipEslint) {
      console.log('=== ESLint Configuration ===');

      // Backup current config
      results.eslint.backup = this.backupConfig('./eslint.config.js');

      // Merge configurations
      const eslintConfig = this.mergeEslintConfig();

      // Validate
      if (this.validateConfig(eslintConfig, 'eslint')) {
        // Write merged config
        results.eslint.success = this.writeConfig(eslintConfig, './eslint.config.js', 'eslint');
      }
    }

    // Process Prettier configuration
    if (!options.skipPrettier) {
      console.log('\n=== Prettier Configuration ===');

      // Backup current config
      results.prettier.backup = this.backupConfig('./.prettierrc.json');

      // Merge configurations
      const prettierConfig = this.mergePrettierConfig();

      // Validate
      if (this.validateConfig(prettierConfig, 'prettier')) {
        // Write merged config
        results.prettier.success = this.writeConfig(prettierConfig, './.prettierrc.json', 'prettier');
      }
    }

    // Summary
    console.log('\n=== Merge Summary ===');
    console.log(`ESLint: ${results.eslint.success ? '✅ Success' : '❌ Failed'}`);
    if (results.eslint.backup) {
      console.log(`  Backup: ${results.eslint.backup}`);
    }

    console.log(`Prettier: ${results.prettier.success ? '✅ Success' : '❌ Failed'}`);
    if (results.prettier.backup) {
      console.log(`  Backup: ${results.prettier.backup}`);
    }

    const overallSuccess = results.eslint.success && results.prettier.success;
    console.log(`\nOverall: ${overallSuccess ? '✅ Success' : '❌ Failed'}`);

    return results;
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const options = {};

  // Parse command line arguments
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--skip-eslint') {
      options.skipEslint = true;
    } else if (arg === '--skip-prettier') {
      options.skipPrettier = true;
    } else if (arg === '--help' || arg === '-h') {
      console.log(`
Configuration Merger Utility

Usage: node scripts/utils/config-merger.js [options]

Options:
  --skip-eslint     Skip ESLint configuration merge
  --skip-prettier   Skip Prettier configuration merge
  --help, -h        Show this help message

Examples:
  node scripts/utils/config-merger.js                    # Merge all configurations
  node scripts/utils/config-merger.js --skip-eslint     # Skip ESLint only
  node scripts/utils/config-merger.js --skip-prettier    # Skip Prettier only
      `);
      process.exit(0);
    }
  }

  const merger = new ConfigMerger();
  const results = await merger.run(options);

  // Exit with appropriate code
  process.exit(results.eslint.success && results.prettier.success ? 0 : 1);
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('❌ Unhandled error:', error);
    process.exit(1);
  });
}

export default ConfigMerger;
