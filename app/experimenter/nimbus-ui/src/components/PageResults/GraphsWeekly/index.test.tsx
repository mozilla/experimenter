/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { act, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import GraphsWeekly from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { GROUP } from "../../../lib/visualization/constants";
import { mockAnalysis } from "../../../lib/visualization/mocks";

describe("GraphsWeekly", () => {
  it("Displays 'Show Graphs' button and updates its label when clicked", async () => {
    const { mock } = mockExperimentQuery("demo-slug");

    render(
      <RouterSlugProvider mocks={[mock]}>
        <GraphsWeekly
          weeklyResults={mockAnalysis().weekly.enrollments}
          outcomeSlug="feature_d"
          outcomeName="Feature D"
          group={GROUP.OTHER}
        />
      </RouterSlugProvider>,
    );
    expect(screen.getByText("Show Graphs")).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByText("Show Graphs"));
    });
    expect(screen.getByText("Hide Graphs")).toBeInTheDocument();
  });
});
