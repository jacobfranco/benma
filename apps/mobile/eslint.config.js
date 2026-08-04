const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');

module.exports = defineConfig([
  expoConfig,
  {
    ignores: ['src/api/schema.d.ts'],
    rules: {
      'import/order': ['error', { 'newlines-between': 'always' }],
    },
  },
]);
