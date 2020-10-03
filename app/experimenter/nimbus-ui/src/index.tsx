/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import ReactDOM from "react-dom";
import App from "./components/App";
import AppErrorBoundary from "./components/AppErrorBoundary";
import "./styles/index.scss";

ReactDOM.render(
  <React.StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>              
  </React.StrictMode>,
  document.getElementById("root"),
);
