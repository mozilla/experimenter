/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableMetricSecondary from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { mockAnalysis } from "../../../lib/visualization/mocks";

describe("TableMetricSecondary", () => {
  it("has the correct headings", () => {
    const EXPECTED_HEADINGS = ["Count", "Relative Improvement"];
    const { mock, experiment } = mockExperimentQuery("demo-slug");

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricSecondary
          results={mockAnalysis()}
          probeSetSlug={experiment.secondaryProbeSets![0]!.slug}
          probeSetDefaultName={experiment.secondaryProbeSets![0]!.name}
          isDefault={false}
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
        <TableMetricSecondary
          results={mockAnalysis()}
          probeSetSlug={experiment.secondaryProbeSets![0]!.slug}
          probeSetDefaultName={experiment.secondaryProbeSets![0]!.name}
          isDefault={false}
        />
      </RouterSlugProvider>,
    );

    const positiveSignificance = screen.queryByTestId("positive-significance");
    const neutralSignificance = screen.queryByTestId("neutral-significance");

    expect(screen.getByTestId("negative-significance")).toBeInTheDocument();
    expect(positiveSignificance).not.toBeInTheDocument();
    expect(neutralSignificance).not.toBeInTheDocument();
  });

  it("has the expected control and treatment labels", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricSecondary
          results={mockAnalysis()}
          probeSetSlug={experiment.secondaryProbeSets![0]!.slug}
          probeSetDefaultName={experiment.secondaryProbeSets![0]!.name}
          isDefault={false}
        />
      </RouterSlugProvider>,
    );

    expect(screen.getAllByText("control")).toHaveLength(2);
    expect(screen.getByText("treatment")).toBeInTheDocument();
  });

  it("shows the negative improvement bar", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricSecondary
          results={mockAnalysis()}
          probeSetSlug={experiment.secondaryProbeSets![0]!.slug}
          probeSetDefaultName={experiment.secondaryProbeSets![0]!.name}
          isDefault={false}
        />
      </RouterSlugProvider>,
    );

    const positiveBlock = screen.queryByTestId("positive-block");
    const neutralBlock = screen.queryByTestId("neutral-block");

    expect(screen.getByTestId("negative-block")).toBeInTheDocument();
    expect(positiveBlock).not.toBeInTheDocument();
    expect(neutralBlock).not.toBeInTheDocument();
  });

  it("shows expected count values", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricSecondary
          results={mockAnalysis()}
          probeSetSlug={experiment.secondaryProbeSets![0]!.slug}
          probeSetDefaultName={experiment.secondaryProbeSets![0]!.name}
          isDefault={false}
        />
      </RouterSlugProvider>,
    );

    expect(screen.queryAllByText("0.02 to 0.08")).toHaveLength(2);
  });

  it("uses the friendly name from the metadata", () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug");
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableMetricSecondary
          results={mockAnalysis()}
          probeSetSlug="feature_d"
          probeSetDefaultName={experiment.secondaryProbeSets![0]!.name}
          isDefault={false}
        />
      </RouterSlugProvider>,
    );

    expect(screen.queryByText("Feature D Friendly Name")).toBeInTheDocument();
  });
});
