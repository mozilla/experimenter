/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Router } from "@reach/router";

import PageHome from "../PageHome";
import PageNew from "../PageNew";

const App = ({ basepath }: { basepath: string }) => {
  return (
    <Router {...{ basepath }}>
      <PageHome path="/" />
      <PageNew path="new" />
    </Router>
  );
};

export default App;
