/* eslint-env node */
module.exports = {
  globals: {},
  testMatch: ["**/__tests__/?(*.)test.ts?(x)"],
  transform: {
    "^.+\\.jsx?$": "babel-jest",
    "^.+\\.tsx?$": "ts-jest",
  },
  moduleNameMapper: {
    "^experimenter-rapid/(.*)$": "<rootDir>/$1",
    "^experimenter-types/(.*)$": "<rootDir>/types/$1",
    "\\.(less|css)$": "identity-obj-proxy",
  },
  setupFiles: ["<rootDir>/jest.setup.ts"],
  setupFilesAfterEnv: ["<rootDir>/jest-env.setup.ts"],
  verbose: true,
  collectCoverage: true,
  collectCoverageFrom: [
    "<rootDir>/**/*.{ts,tsx}",
    "!<rootDir>/__tests__/**/*.{ts,tsx}",
    "!<rootDir>/types/**/*.{ts,tsx}",
    "!<rootDir>/index.tsx",
  ],
  coverageReporters: ["text"],
  coverageThreshold: {
    global: {
      lines: 100,
    },
  },
};
