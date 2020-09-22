module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  parserOptions: {
    createDefaultProgram: true,
    ecmaVersion: 2019,
    sourceType: "module",
  },
  env: {
    browser: true,
    es6: true,
    node: true,
  },
  extends: ["eslint:recommended"],
  plugins: ["@typescript-eslint", "svelte3", "import", "prettier"],
  rules: {
    "import/first": "off",
    "import/prefer-default-export": "off",
    "import/no-mutable-exports": 0,
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
    "no-param-reassign": [
      "error",
      { props: true, ignorePropertyModificationsFor: ["draft"] },
    ],
  },
  overrides: [
    {
      files: ["**/*.js"],
      extends: ["prettier"],
      plugins: ["prettier"],
      rules: {
        "prettier/prettier": "error",
      },
    },
    {
      files: ["**/*.svelte"],
      processor: "svelte3/svelte3",

      // Turn off all rules that might conflict with Prettier.[1] Note that this
      // does not warn if a Svelte file disobeys Prettier rules. That's what the
      // Prettier *plugin* does, but at the time of this writing, the
      // eslint-plugin-svelte3 plugin discourages the use of the Prettier
      // plugin for Svelte files.[2]
      //
      // [1] https://github.com/prettier/eslint-config-prettier
      // [2] https://github.com/sveltejs/eslint-plugin-svelte3/blob/6900d670c9e85509b2d21decd91f1e75f7934596/OTHER_PLUGINS.md#eslint-plugin-prettier
      extends: ["prettier"],

      rules: {
        "prefer-const": "off",

        // Disable rules that do not work correctly with eslint-plugin-svelte3
        //
        // https://github.com/sveltejs/eslint-plugin-svelte3/blob/6900d670c9e85509b2d21decd91f1e75f7934596/OTHER_PLUGINS.md#eslint-plugin-import
        "import/first": "off",
        "import/no-duplicates": "off",
        "import/no-mutable-exports": "off",
        "import/no-unresolved": "off",

        // Temporarily work around a bug in eslint-plugin-svelte3.
        //
        // https://github.com/sveltejs/eslint-plugin-svelte3/issues/41#issuecomment-572503966
        "no-multiple-empty-lines": ["error", { max: 2, maxBOF: 2, maxEOF: 0 }],
      },
    },
  ],
};
