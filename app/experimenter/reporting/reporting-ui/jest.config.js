module.exports = {
  coverageThreshold: { global: { statements: 100 } },
  moduleNameMapper: {
    "^experimenter-reporting/(.*)$": "<rootDir>/$1",
    "\\.(less|css)$": "identity-obj-proxy",
  },
  testEnvironment: "jest-environment-jsdom-sixteen",
  setupFiles: ["./setupJest.js"],
};
