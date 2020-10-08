/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import ReactDOM from "react-dom";
import App from "./components/App";
import "./styles/index.scss";
import { readConfig } from "./lib/config";

try {
  const root = document.getElementById("root")!;
  readConfig(root);

  ReactDOM.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
    root
  );
} catch (error) {
  console.error("Error initializing Nimbus", error);
}
