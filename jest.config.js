const path = require('path')

module.exports = {
    preset: 'ts-jest', // enables type checking as part of jest testing
    rootDir: path.resolve(__dirname, 'srcmedia'),
    testRegex: '^.+\\.(test|spec)\\.tsx?$',
    moduleFileExtensions: ['js', 'jsx', 'ts', 'tsx', 'json', 'node'],
    coverageDirectory: '<rootDir>/coverage',
    collectCoverageFrom: [
        "ts/lib/*.{ts,tsx}", // test base classes
        "ts/components/*.{ts,tsx}", // test custom components
        '!**/node_modules/**', // don't cover pulled-in dependencies
    ]
}
