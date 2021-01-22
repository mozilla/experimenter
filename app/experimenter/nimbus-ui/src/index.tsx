/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { ApolloProvider } from "@apollo/client";
import React from "react";
import ReactDOM from "react-dom";
import App from "./components/App";
import AppErrorBoundary from "./components/AppErrorBoundary";
import { BASE_PATH } from "./lib/constants";
import { createApolloClient } from "./services/apollo";
import config, { readConfig } from "./services/config";
import sentryMetrics from "./services/sentry";
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
          <App basepath={BASE_PATH} />
        </ApolloProvider>
      </AppErrorBoundary>
    </React.StrictMode>,
    root,
  );
} catch (error) {
  console.error("Error initializing Nimbus", error);
}
