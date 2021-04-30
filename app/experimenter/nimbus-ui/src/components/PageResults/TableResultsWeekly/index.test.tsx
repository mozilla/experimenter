/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import TableResultsWeekly from ".";
import { RouterSlugProvider } from "../../../lib/test-utils";
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

describe("TableResultsWeekly", () => {
  it("has the correct headings", () => {
    const EXPECTED_HEADINGS = ["Retention", "Search", "Days of Use"];

    render(
      <RouterSlugProvider>
        <TableResultsWeekly
          hasOverallResults
          metricsList={HIGHLIGHTS_METRICS_LIST}
          {...{ weeklyResults, sortedBranches }}
        />
      </RouterSlugProvider>,
    );

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("behaves as expected when clicked", () => {
    const HIDE_TEXT = "Hide Weekly Data";
    const SHOW_TEXT = "Show Weekly Data";

    render(
      <RouterSlugProvider>
        <TableResultsWeekly
          hasOverallResults={false}
          metricsList={HIGHLIGHTS_METRICS_LIST}
          {...{ weeklyResults, sortedBranches }}
        />
      </RouterSlugProvider>,
    );

    expect(screen.getByText(HIDE_TEXT)).toBeInTheDocument();
    fireEvent.click(screen.getByText(HIDE_TEXT));
    expect(screen.getByText(SHOW_TEXT)).toBeInTheDocument();
  });
});
