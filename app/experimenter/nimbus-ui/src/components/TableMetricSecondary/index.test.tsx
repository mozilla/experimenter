/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import TableMetricSecondary from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockAnalysis } from "../../lib/visualization/mocks";
import { mockExperimentQuery } from "../../lib/mocks";

describe("TableMetricSecondary", () => {
  it("has the correct headings", async () => {
    const EXPECTED_HEADINGS = ["Count", "Relative Improvement"];
    const { mock, data } = mockExperimentQuery("demo-slug");

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricSecondary
          results={mockAnalysis().overall}
          probeSet={data!.primaryProbeSets![0]!}
        />
      </RouterSlugProvider>,
    );

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("has correctly labelled result significance", async () => {
    const { mock, data } = mockExperimentQuery("demo-slug");
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricSecondary
          results={mockAnalysis().overall}
          probeSet={data!.primaryProbeSets![0]!}
        />
      </RouterSlugProvider>,
    );

    const negativeSignificance = screen.queryByTestId("negative-significance");
    const neutralSignificance = screen.queryByTestId("neutral-significance");

    expect(screen.getByTestId("positive-significance")).toBeInTheDocument();
    expect(negativeSignificance).not.toBeInTheDocument();
    expect(neutralSignificance).not.toBeInTheDocument();
  });

  it("has the expected control and treatment labels", async () => {
    const { mock, data } = mockExperimentQuery("demo-slug");
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricSecondary
          results={mockAnalysis().overall}
          probeSet={data!.primaryProbeSets![0]!}
        />
      </RouterSlugProvider>,
    );

    expect(screen.getAllByText("control")).toHaveLength(2);
    expect(screen.getByText("treatment")).toBeInTheDocument();
  });

  it("shows the positive improvement bar", async () => {
    const { mock, data } = mockExperimentQuery("demo-slug");
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricSecondary
          results={mockAnalysis().overall}
          probeSet={data!.primaryProbeSets![0]!}
        />
      </RouterSlugProvider>,
    );

    const negativeBlock = screen.queryByTestId("negative-block");
    const neutralBlock = screen.queryByTestId("neutral-block");

    expect(screen.getByTestId("positive-block")).toBeInTheDocument();
    expect(negativeBlock).not.toBeInTheDocument();
    expect(neutralBlock).not.toBeInTheDocument();
  });
});
