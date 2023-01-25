/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { ApolloProvider } from "@apollo/client";
import React from "react";
import ReactDOM from "react-dom";
import App from "src/components/App";
import AppErrorBoundary from "src/components/AppErrorBoundary";
import { createApolloClient } from "src/services/apollo";
import config, { readConfig } from "src/services/config";
import sentryMetrics from "src/services/sentry";
import "src/styles/index.scss";

try {
  const root = document.getElementById("root")!;
  readConfig(root);

  if (config.sentry_dsn) {
    sentryMetrics.configure(config.sentry_dsn, config.version);
  }

  ReactDOM.render(
    <React.StrictMode>
      <AppErrorBoundary>
        <ApolloProvider client={createApolloClient()}>
          <App />
        </ApolloProvider>
      </AppErrorBoundary>
    </React.StrictMode>,
    root,
  );
} catch (error) {
  console.error("Error initializing Nimbus", error);
}
