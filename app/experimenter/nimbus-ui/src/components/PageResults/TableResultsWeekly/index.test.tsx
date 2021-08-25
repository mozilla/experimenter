/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import TableResultsWeekly from ".";
import { MockResultsContextProvider } from "../../../lib/mocks";
import { BRANCH_COMPARISON } from "../../../lib/visualization/constants";

describe("TableResultsWeekly", () => {
  it("renders as expected with relative uplift branch comparison (default)", () => {
    render(
      <MockResultsContextProvider>
        <TableResultsWeekly />,
      </MockResultsContextProvider>,
    );

    const EXPECTED_HEADINGS = ["Retention", "Search", "Days of Use"];
    const EXPECTED_WEEKS = ["Week 1", "Week 2"];

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
    EXPECTED_WEEKS.forEach((week) => {
      expect(screen.getAllByText(week)).toHaveLength(EXPECTED_HEADINGS.length);
    });

    // control branches have this text for every week
    expect(screen.getAllByText("(baseline)")).toHaveLength(
      EXPECTED_HEADINGS.length * EXPECTED_WEEKS.length,
    );
    expect(screen.getAllByText("-45.5% to 51%", { exact: false })).toHaveLength(
      2,
    );
  });

  it("renders as expected with absolute branch comparison", () => {
    render(
      <MockResultsContextProvider>
        <TableResultsWeekly branchComparison={BRANCH_COMPARISON.ABSOLUTE} />
      </MockResultsContextProvider>,
    );

    expect(
      screen.getAllByText("2.4% to 8.4% (baseline)", { exact: false }),
    ).toHaveLength(2);
  });

  it("behaves as expected when clicked", () => {
    const HIDE_TEXT = "Hide Weekly Data";
    const SHOW_TEXT = "Show Weekly Data";

    render(
      <MockResultsContextProvider>
        <TableResultsWeekly />,
      </MockResultsContextProvider>,
    );

    fireEvent.click(screen.getByText(SHOW_TEXT));
    expect(screen.getByText(HIDE_TEXT)).toBeInTheDocument();
    fireEvent.click(screen.getByText(HIDE_TEXT));
    expect(screen.getByText(SHOW_TEXT)).toBeInTheDocument();
  });
});
