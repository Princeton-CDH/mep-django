const path = require('path')

module.exports = {
  rootDir: path.resolve(__dirname),
  testURL: 'http://localhost/',
  moduleFileExtensions: ['js', 'json', 'vue'],
  moduleNameMapper: {'^@/(.*)$': '<rootDir>/js/src/$1'},
  transform: {
    '^.+\\.js$': '<rootDir>/node_modules/babel-jest',
    '.*\\.(vue)$': '<rootDir>/node_modules/vue-jest'
  },
  testPathIgnorePatterns: [
    '<rootDir>/js/test/e2e'
  ],
  coverageDirectory: '<rootDir>/js/test/unit/coverage',
  collectCoverageFrom: [
    'js/src/**/*.{js,vue}',
    'js/src/*.{js,vue}',
    '!**/node_modules/**'
  ]
}
