/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableMetricPrimary from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { mockAnalysis } from "../../../lib/visualization/mocks";

describe("TableMetricPrimary", () => {
  it("has the correct headings", () => {
    const EXPECTED_HEADINGS = [
      "Conversions / Total Users",
      "Conversion Rate",
      "Relative Improvement",
    ];
    const { mock, experiment } = mockExperimentQuery("demo-slug");

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricPrimary
          results={mockAnalysis().overall}
          outcome={experiment.primaryOutcomes![0]!}
        />
      </RouterSlugProvider>,
    );

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("has correctly labelled result significance", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricPrimary
          results={mockAnalysis().overall}
          outcome={experiment.primaryOutcomes![0]!}
        />
      </RouterSlugProvider>,
    );

    const negativeSignificance = screen.queryByTestId("negative-significance");
    const neutralSignificance = screen.queryByTestId("neutral-significance");

    expect(screen.getByTestId("positive-significance")).toBeInTheDocument();
    expect(negativeSignificance).not.toBeInTheDocument();
    expect(neutralSignificance).not.toBeInTheDocument();
  });

  it("has the expected control and treatment labels", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricPrimary
          results={mockAnalysis().overall}
          outcome={experiment.primaryOutcomes![0]!}
        />
      </RouterSlugProvider>,
    );

    expect(screen.getAllByText("control")).toHaveLength(2);
    expect(screen.getByText("treatment")).toBeInTheDocument();
  });

  it("shows the positive improvement bar", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricPrimary
          results={mockAnalysis().overall}
          outcome={experiment.primaryOutcomes![0]!}
        />
      </RouterSlugProvider>,
    );

    const negativeBlock = screen.queryByTestId("negative-block");
    const neutralBlock = screen.queryByTestId("neutral-block");

    expect(screen.getByTestId("positive-block")).toBeInTheDocument();
    expect(negativeBlock).not.toBeInTheDocument();
    expect(neutralBlock).not.toBeInTheDocument();
  });

  it("shows the negative improvement bar", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: ["feature_b"],
    });

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricPrimary
          results={mockAnalysis().overall}
          outcome={experiment.primaryOutcomes![0]!}
        />
      </RouterSlugProvider>,
    );

    const positiveBlock = screen.queryByTestId("positive-block");
    const neutralBlock = screen.queryByTestId("neutral-block");

    expect(screen.getByTestId("negative-block")).toBeInTheDocument();
    expect(positiveBlock).not.toBeInTheDocument();
    expect(neutralBlock).not.toBeInTheDocument();
  });

  it("shows the neutral improvement bar", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: ["feature_c"],
    });

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricPrimary
          results={mockAnalysis().overall}
          outcome={experiment.primaryOutcomes![0]!}
        />
      </RouterSlugProvider>,
    );

    const negativeBlock = screen.queryByTestId("negative-block");
    const positiveBlock = screen.queryByTestId("positive-block");

    expect(screen.getByTestId("neutral-block")).toBeInTheDocument();
    expect(negativeBlock).not.toBeInTheDocument();
    expect(positiveBlock).not.toBeInTheDocument();
  });
});
