/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import TableResultsWeekly from ".";
import { MockResultsContextProvider } from "../../../lib/mocks";
import {
  BRANCH_COMPARISON,
  HIGHLIGHTS_METRICS_LIST,
} from "../../../lib/visualization/constants";

storiesOf("pages/Results/TableResultsWeekly", module)
  .addDecorator(withLinks)
  .add("with relative uplift comparison", () => {
    return (
      <MockResultsContextProvider>
        <TableResultsWeekly metricsList={HIGHLIGHTS_METRICS_LIST} />
      </MockResultsContextProvider>
    );
  })
  .add("with absolute comparison", () => {
    return (
      <MockResultsContextProvider>
        <TableResultsWeekly
          metricsList={HIGHLIGHTS_METRICS_LIST}
          branchComparison={BRANCH_COMPARISON.ABSOLUTE}
        />
      </MockResultsContextProvider>
    );
  });
