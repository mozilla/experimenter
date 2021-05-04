/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import TableResultsWeekly from ".";
import { HIGHLIGHTS_METRICS_LIST } from "../../../lib/visualization/constants";
import { weeklyMockAnalysis } from "../../../lib/visualization/mocks";
import { getSortedBranches } from "../../../lib/visualization/utils";

const weeklyResults = weeklyMockAnalysis();
const sortedBranches = getSortedBranches({
  show_analysis: true,
  daily: null,
  weekly: weeklyResults,
  overall: null,
});

storiesOf("pages/Results/TableResultsWeekly", module)
  .addDecorator(withLinks)
  .add("basic", () => {
    return (
      <TableResultsWeekly
        {...{ weeklyResults, sortedBranches }}
        hasOverallResults
        metricsList={HIGHLIGHTS_METRICS_LIST}
      />
    );
  });
