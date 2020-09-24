const baseSettings = {
  env: {
    node: true,
    browser: true,
    es6: true,
  },
  parser: "@typescript-eslint/parser",
  plugins: ["import"],
  extends: [
    "eslint:recommended",
    "plugin:prettier/recommended",
    "plugin:react/recommended",
  ],
  rules: {
    "import/order": [
      "error",
      {
        groups: ["builtin", "external", "internal", "parent"],
        pathGroups: [
          {
            pattern: "experimenter-rapid/**",
            group: "parent",
          },
          {
            pattern: "experimenter-types/**",
            group: "parent",
          },
        ],
        pathGroupsExcludedImportTypes: ["builtin"],
        alphabetize: {
          order: "asc",
          caseInsensitive: true,
        },
        "newlines-between": "always",
      },
    ],
    "react/jsx-curly-brace-presence": ["error", "never"],
    "react/jsx-sort-props": [
      "error",
      {
        callbacksLast: true,
        shorthandFirst: true,
        ignoreCase: true,
        reservedFirst: true,
      },
    ],
    eqeqeq: ["error", "always"],
    "prefer-const": "error",
    "lines-between-class-members": ["error", "always"],
    "padding-line-between-statements": [
      "error",
      {
        blankLine: "always",
        prev: "multiline-block-like",
        next: "*",
      },
    ],
    "react/prop-types": [0],
  },
  settings: {
    react: {
      version: "detect",
    },
  },
};

module.exports = {
  ...baseSettings,
  overrides: [
    {
      files: ["*.ts", "*.tsx"],
      plugins: [...baseSettings.plugins, "@typescript-eslint"],
      extends: [
        ...baseSettings.extends,
        "plugin:@typescript-eslint/eslint-recommended",
        "plugin:@typescript-eslint/recommended",
        "prettier/@typescript-eslint",
      ],
      rules: {
        ...baseSettings.rules,
        "react/prop-types": [0],
      },
    },
  ],
};
