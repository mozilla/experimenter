/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import GraphsWeekly from ".";
import { MockResultsContextProvider } from "../../../lib/mocks";
import { GROUP } from "../../../lib/visualization/constants";

storiesOf("pages/Results/GraphsWeekly", module)
  .addDecorator(withLinks)
  .add("with two data points", () => {
    return (
      <MockResultsContextProvider>
        <GraphsWeekly
          outcomeSlug="feature_d"
          outcomeName="Feature D"
          group={GROUP.OTHER}
        />
      </MockResultsContextProvider>
    );
  });
