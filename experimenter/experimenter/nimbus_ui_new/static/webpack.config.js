const path = require("path");
const webpack = require("webpack");

module.exports = {
  entry: {
    app: "./js/index.js",
    experiment_list: "./js/scripts/experiment_list.js",
    theme: "./js/scripts/theme.js",
  },
  output: {
    filename: "[name].bundle.js",
    path: path.resolve(__dirname, "dist"),
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
      $: "jquery",
      jQuery: "jquery",
      "window.jQuery": "jquery",
      Popper: ["popper.js", "default"],
      bootstrap: "bootstrap",
    }),
  ],
  resolve: {
    alias: {
      jquery: "jquery/src/jquery",
    },
  },
  mode: "production",
};
