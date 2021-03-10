/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import GraphsWeekly from ".";
import { mockAnalysis } from "../../../lib/visualization/mocks";

storiesOf("pages/Results/GraphsWeekly", module)
  .addDecorator(withLinks)
  .add("with two data points", () => {
    return (
      <GraphsWeekly
        weeklyResults={mockAnalysis().weekly}
        outcomeSlug="feature_d"
        outcomeName="Feature D"
      />
    );
  });
