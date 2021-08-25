/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableWeekly from ".";
import { MockResultsContextProvider } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { BRANCH_COMPARISON, GROUP } from "../../../lib/visualization/constants";
import {
  mockAnalysis,
  weeklyMockAnalysis,
  WEEKLY_IDENTITY,
  WEEKLY_TREATMENT,
  WONKY_WEEKLY_TREATMENT,
} from "../../../lib/visualization/mocks";

describe("TableWeekly", () => {
  it("has the correct headings", () => {
    const EXPECTED_HEADINGS = ["Week 1", "Week 2", "Week 5"];
    const modifications = {
      treatment: {
        is_control: false,
        branch_data: {
          search_metrics: {
            search_count: WEEKLY_TREATMENT,
          },
          other_metrics: {
            identity: WEEKLY_IDENTITY,
            feature_d: WEEKLY_TREATMENT,
            retained: WONKY_WEEKLY_TREATMENT,
            days_of_use: WEEKLY_TREATMENT,
          },
        },
      },
    };

    const analysis = mockAnalysis({
      weekly: weeklyMockAnalysis(modifications),
    });

    render(
      <RouterSlugProvider>
        <MockResultsContextProvider {...{ analysis }}>
          <TableWeekly
            metricKey="retained"
            metricName="Retention"
            group={GROUP.OTHER}
            branchComparison={BRANCH_COMPARISON.UPLIFT}
          />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("shows error text when metric data isn't available", () => {
    const ERROR_TEXT = "Some Made Up Metric is not available";

    render(
      <RouterSlugProvider>
        <MockResultsContextProvider>
          <TableWeekly
            branchComparison={BRANCH_COMPARISON.ABSOLUTE}
            metricKey="fake"
            metricName="Some Made Up Metric"
            group={GROUP.OTHER}
          />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );

    expect(screen.getAllByText(ERROR_TEXT)).toHaveLength(2);
  });
});
