/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableHighlights from "src/components/PageResults/TableHighlights";
import { mockExperimentQuery, MockResultsContextProvider } from "src/lib/mocks";
import { RouterSlugProvider } from "src/lib/test-utils";
import { BRANCH_COMPARISON } from "src/lib/visualization/constants";

const { mock, experiment } = mockExperimentQuery("demo-slug");

describe("TableHighlights", () => {
  it("has participants shown for each variant", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableHighlights {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );

    expect(
      screen.getAllByText("participants", {
        exact: false,
      }),
    ).toHaveLength(2);
  });

  it("has an expected branch description", () => {
    const branchDescription = experiment.referenceBranch!.description;
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableHighlights {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );

    expect(screen.getByText(branchDescription)).toBeInTheDocument();
  });

  it("has correctly labelled result significance", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableHighlights {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );

    expect(screen.getByTestId("positive-significance")).toBeInTheDocument();
    expect(screen.getByTestId("negative-significance")).toBeInTheDocument();
    expect(screen.queryAllByTestId("neutral-significance")).toHaveLength(2);
  });

  it("has the expected control and treatment labels", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableHighlights {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );

    expect(screen.getByText("control")).toBeInTheDocument();
    expect(screen.getByText("treatment")).toBeInTheDocument();
  });

  it("with relative comparison, renders expected values", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableHighlights {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );
    expect(screen.getAllByText("-45.5% to 51%", { exact: false })).toHaveLength(
      4,
    );
  });

  it("with absolute comparison, renders expected values", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableHighlights
            {...{ experiment }}
            branchComparison={BRANCH_COMPARISON.ABSOLUTE}
          />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );

    expect(
      screen.getAllByText("(2.4% to 8.2%)", { exact: false }),
    ).toHaveLength(1);
    expect(screen.getAllByText("0.02 to 0.08", { exact: false })).toHaveLength(
      5,
    );
  });
});
