/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableHighlights from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { mockAnalysis } from "../../../lib/visualization/mocks";

const { mock, experiment } = mockExperimentQuery("demo-slug");

describe("TableHighlights", () => {
  it("has participants for all users shown for each variant", () => {
    const EXPECTED_LABELS = ["participants", "All Users"];

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableHighlights
          primaryProbeSets={experiment.primaryProbeSets!}
          results={mockAnalysis().overall}
        />
      </RouterSlugProvider>,
    );

    EXPECTED_LABELS.forEach((label) => {
      expect(
        screen.getAllByText(label, {
          exact: false,
        }),
      ).toHaveLength(2);
    });
  });

  it("has correctly labelled result significance", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableHighlights
          primaryProbeSets={experiment.primaryProbeSets!}
          results={mockAnalysis().overall}
        />
      </RouterSlugProvider>,
    );

    expect(screen.getByTestId("positive-significance")).toBeInTheDocument();
    expect(screen.getByTestId("negative-significance")).toBeInTheDocument();
    expect(screen.queryAllByTestId("neutral-significance")).toHaveLength(2);
  });

  it("has the expected control and treatment labels", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableHighlights
          primaryProbeSets={experiment.primaryProbeSets!}
          results={mockAnalysis().overall}
        />
      </RouterSlugProvider>,
    );

    expect(screen.getByText("control")).toBeInTheDocument();
    expect(screen.getByText("treatment")).toBeInTheDocument();
  });
});
