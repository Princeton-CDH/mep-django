const path = require('path')

module.exports = {
    rootDir: path.resolve(__dirname, 'srcmedia'),
    testURL: 'http://localhost/',
    moduleFileExtensions: ['js', 'json', 'vue'],
    modulePaths: [
        '<rootDir>/js/modules',
        '<rootDir>/js/components',
    ],
    moduleNameMapper: {
        '^vue$': path.resolve(__dirname, 'node_modules/vue/dist/vue.common.js'), // use the commonjs version of vue
    },
    transform: {
        "^.+\\.vue$": "vue-jest", // preprocess vue SFCs before testing
        "^.+\\.js$": "babel-jest", // preprocess es6+ to es5 before testing
    },
    testPathIgnorePatterns: ['<rootDir>/test/e2e'],
    collectCoverage: true,
    coverageDirectory: '<rootDir>/test/unit/coverage',
    collectCoverageFrom: [
        '<rootDir>/js/modules/**',
        '<rootDir>/js/components/**',
        '!**/node_modules/**',
    ]
}
