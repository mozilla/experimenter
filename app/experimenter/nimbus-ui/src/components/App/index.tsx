/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import AppLayout from "../AppLayout";
import { Router } from "@reach/router";

import PageHome from "../PageHome";
import PageExperimentNew from "../PageExperimentNew";

const App = ({ basepath }: { basepath: string }) => {
  return (
    <div data-testid="app">
      <AppLayout>
        <Router {...{ basepath }}>
          <PageHome path="/" />
          <PageExperimentNew path="new" />
        </Router>
      </AppLayout>
    </div>
  );
};

export default App;
