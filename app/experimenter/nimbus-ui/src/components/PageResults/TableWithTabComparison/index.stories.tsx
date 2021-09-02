/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import TableWithTabComparison from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import TableHighlights from "../TableHighlights";
import TableResults from "../TableResults";
import TableResultsWeekly from "../TableResultsWeekly";
import { Subject } from "./mocks";

export default {
  title: "pages/Results/TableWithTabComparison",
  component: TableWithTabComparison,
};

const { experiment } = mockExperimentQuery("demo-slug");

export const WithHighlightsTable = () => (
  <Subject
    Table={TableHighlights}
    {...{ experiment }}
    className="mb-2 border-top-0"
  />
);

export const WithResultsTable = () => (
  <Subject
    Table={TableResults}
    {...{ experiment }}
    className="rounded-bottom mb-3 border-top-0"
  />
);

export const WithResultsWeeklyTable = () => (
  <Subject Table={TableResultsWeekly} />
);
