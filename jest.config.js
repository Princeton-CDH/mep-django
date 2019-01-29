const path = require('path')

module.exports = {
    rootDir: path.resolve(__dirname),
    testURL: 'http://localhost/',
    moduleFileExtensions: ['js', 'json', 'vue'],
    modulePaths: ['<rootDir>/js/src/components'],
    moduleNameMapper: {
        '^vue$': '<rootDir>/node_modules/vue/dist/vue.common.js', // use the commonjs version of vue
    },
    transform: {
        "^.+\\.js$": "babel-jest", // preprocess es6+ to es5 before testing
        "^.+\\.vue$": "vue-jest", // preprocess vue SFCs before testing
    },
    testPathIgnorePatterns: ['<rootDir>/js/test/e2e'],
    collectCoverage: true,
    coverageDirectory: '<rootDir>/js/test/unit/coverage',
    collectCoverageFrom: [
        '<rootDir>/js/src/components/*.vue',
        '!**/node_modules/**',
    ]
}
