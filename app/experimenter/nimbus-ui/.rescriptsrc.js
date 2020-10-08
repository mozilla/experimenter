/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

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

  return config;
}];
