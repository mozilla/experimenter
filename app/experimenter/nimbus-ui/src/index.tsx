/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import ReactDOM from "react-dom";
import { ApolloProvider } from "@apollo/client";
import App from "./components/App";
import AppErrorBoundary from "./components/AppErrorBoundary";
import config, { readConfig } from "./services/config";
import sentryMetrics from "./services/sentry";
import { createApolloClient } from "./services/apollo";
import "./styles/index.scss";

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
          <App basepath="/experiments/nimbus" />
        </ApolloProvider>
      </AppErrorBoundary>
    </React.StrictMode>,
    root,
  );
} catch (error) {
  console.error("Error initializing Nimbus", error);
}
