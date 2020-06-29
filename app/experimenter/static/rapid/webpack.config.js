/* eslint-env node */
const path = require("path");

const MODE_DEVELOPMENT = "development";
const MODE_PRODUCTION = "production";

module.exports = (env, argv = {}) => {
  const mode = argv.mode || MODE_DEVELOPMENT;

  const output = {
    filename: "[name].js",
    path: path.resolve(__dirname, "../assets/rapid"),
    publicPath: "/",
  };

  const plugins = [];

  const rules = [
    {
      test: /\.[jt]sx?$/,
      include: [path.resolve(__dirname)],
      use: ["babel-loader"],
    },
  ];

  return {
    mode,
    devtool: mode === MODE_PRODUCTION ? "source-map" : "eval-source-map",
    entry: {
      main: path.join(__dirname, "index.tsx"),
    },
    output,
    resolve: {
      alias: {
        "experimenter-rapid": path.resolve(__dirname),
        "experimenter-types": path.resolve(__dirname, "types"),
      },
      extensions: [".tsx", ".ts", ".js"],
    },
    plugins,
    module: {
      rules,
    },
    watchOptions: {
      poll: 1000,
      aggregateTimeout: 1000,
    },
  };
};
