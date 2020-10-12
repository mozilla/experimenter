/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import AppLayoutExperimentEdit from ".";

storiesOf("components/AppLayoutExperimentEdit", module).add("default", () => (
  <div data-testid="app" style={{ height: "100vh" }}>
    <AppLayoutExperimentEdit>
      <p>App contents go here</p>
    </AppLayoutExperimentEdit>
  </div>
));
