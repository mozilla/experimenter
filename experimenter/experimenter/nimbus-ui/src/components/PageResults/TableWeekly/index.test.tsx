/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableWeekly from "src/components/PageResults/TableWeekly";
import { MockResultsContextProvider } from "src/lib/mocks";
import { RouterSlugProvider } from "src/lib/test-utils";
import { BRANCH_COMPARISON, GROUP } from "src/lib/visualization/constants";
import {
  mockAnalysis,
  weeklyMockAnalysis,
  WEEKLY_EXTRA_LONG,
  WEEKLY_IDENTITY,
  WEEKLY_TREATMENT,
  WONKY_WEEKLY_TREATMENT,
} from "src/lib/visualization/mocks";

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
      weekly: { enrollments: { all: weeklyMockAnalysis(modifications) } },
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

  it("sorts week indices numerically", () => {
    const modifications = {
      treatment: {
        is_control: false,
        branch_data: {
          other_metrics: {
            identity: WEEKLY_EXTRA_LONG,
            retained: WEEKLY_EXTRA_LONG,
          },
        },
      },
    };

    const analysis = mockAnalysis({
      weekly: { enrollments: { all: weeklyMockAnalysis(modifications) } },
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

    const weekHeadings = screen.getAllByRole("columnheader").slice(1); // Exclude the first column

    const weekIndices = weekHeadings.map((heading) => {
      const weekText = heading.textContent?.replace("Week ", "");
      return weekText ? parseInt(weekText, 10) : NaN;
    });

    expect(weekIndices).toEqual(weekIndices.slice().sort((a, b) => a - b));
  });
});
