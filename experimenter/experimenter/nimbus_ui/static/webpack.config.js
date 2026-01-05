const path = require("path");
const webpack = require("webpack");
const nodeModulesPath = path.resolve(__dirname, "../../../node_modules");

module.exports = {
  entry: {
    app: "./js/index.js",
    experiment_home: "./js/experiment_home.js",
    experiment_list: "./js/experiment_list.js",
    review_controls: "./js/review_controls.js",
    edit_audience: "./js/edit_audience.js",
    edit_branches: "./js/edit_branches.js",
    experiment_detail: "./js/experiment_detail.js",
    branch_detail: "./js/branch_detail.js",
    features_page: "./js/features_page.js",
  },
  output: {
    filename: "[name].bundle.js",
    path: path.resolve(__dirname, "dist"),
  },
  resolve: {
    alias: {
      "@codemirror/state": path.resolve(nodeModulesPath, "@codemirror/state"),
      "@codemirror/view": path.resolve(nodeModulesPath, "@codemirror/view"),
      "@codemirror/merge": path.resolve(nodeModulesPath, "@codemirror/merge"),
      "@codemirror/lang-json": path.resolve(
        nodeModulesPath,
        "@codemirror/lang-json",
      ),
      codemirror: path.resolve(nodeModulesPath, "codemirror"),
    },
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
      },
      {
        test: /\.scss$/,
        use: ["style-loader", "css-loader", "sass-loader"],
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
        },
      },
    ],
  },
  plugins: [
    new webpack.ProvidePlugin({
      bootstrap: "bootstrap",
    }),
  ],
  mode: "production",
};
