/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const SentryWebpackPlugin = require("@sentry/webpack-plugin");

// Rescripts allows us modify the default CRA
// Webpack config without needing to eject.
// Check out the README for how to use this file.

module.exports = [(config) => {
  // Disable code splitting entirely
  config.optimization.runtimeChunk = false;
  config.optimization.splitChunks = {
    cacheGroups: {
      default: false,
    },
  };

  // Always use a consistent output name, without
  // contenthash, so we can reliably locate it
  // from within a Django template
  config.output.filename = "static/js/[name].js";
  // We need to do this for CSS as well
  config.plugins[
    config.plugins.findIndex((p) => p.constructor.name === 'MiniCssExtractPlugin')
  ] = new MiniCssExtractPlugin({
    filename: 'static/css/[name].css',
  });

  if (process.env.SENTRY_UPLOAD_SOURCEMAPS && process.env.SENTRY_AUTH_TOKEN) {
    let versionInfo = null;
    try {
      versionInfo = require("../../version.json");
    } catch (e) {
      /* no-op */
    }
    if (versionInfo) {
      config.plugins.push(
        new SentryWebpackPlugin({
          authToken: process.env.SENTRY_AUTH_TOKEN,
          org: process.env.SENTRY_ORG,
          project: process.env.SENTRY_PROJECT,
          release: versionInfo.commit,
          include: "./build",
          urlPrefix: "~/static/nimbus",
        })
      );
    }
  }

  return config;
}];
