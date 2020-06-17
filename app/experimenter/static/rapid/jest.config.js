/* eslint-env node */
module.exports = {
  globals: {},
  transform: {
    "^.+\\.[jt]sx?$": "babel-jest",
  },
  moduleNameMapper: {
    "^experimenter-rapid/(.*)$": "<rootDir>/$1",
    "\\.(less|css)$": "identity-obj-proxy",
  },
  setupFiles: ["<rootDir>/jest.setup.js"],
  setupFilesAfterEnv: ["<rootDir>/jest-env.setup.js"],
  verbose: true,
  collectCoverage: true,
  collectCoverageFrom: ["<rootDir>/**/*.{ts,tsx}", "!<rootDir>/index.tsx"],
  coverageReporters: ["text"],
  coverageThreshold: {
    global: {
      lines: 100,
    },
  },
};
