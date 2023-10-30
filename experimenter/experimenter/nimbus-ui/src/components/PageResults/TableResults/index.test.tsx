/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableResults from "src/components/PageResults/TableResults";
import { mockExperimentQuery, MockResultsContextProvider } from "src/lib/mocks";
import { RouterSlugProvider } from "src/lib/test-utils";
import { BRANCH_COMPARISON } from "src/lib/visualization/constants";
import { mockIncompleteAnalysis } from "src/lib/visualization/mocks";
import { NimbusExperimentApplicationEnum } from "src/types/globalTypes";

const { mock, experiment } = mockExperimentQuery("demo-slug");

describe("TableResults", () => {
  it("renders correct headings", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableResults {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );
    const EXPECTED_HEADINGS = [
      "2-Week Browser Retention",
      "Mean Searches Per User",
      "Qualified Cumulative Days of Use",
      "Total Users",
    ];

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("renders correct headings for non-desktop experiments", () => {
    const { experiment: ios_experiment } = mockExperimentQuery("demo-slug", {
      application: NimbusExperimentApplicationEnum.IOS,
    });
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableResults experiment={ios_experiment} />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );
    const EXPECTED_HEADINGS = [
      "2-Week Browser Retention",
      "Mean Searches Per User",
      "Overall Mean Days of Use Per User",
      "Total Users",
    ];

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("with relative comparison, renders the expected variant, comparison, and user count", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableResults {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );

    expect(screen.getAllByText("-45.5% to 51%", { exact: false })).toHaveLength(
      4,
    );
    expect(screen.getByText("198")).toBeInTheDocument();
    expect(screen.getByText("45%")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
    expect(screen.getByText("55%")).toBeInTheDocument();
    expect(screen.getByText("control")).toBeInTheDocument();
    expect(screen.getByText("treatment")).toBeInTheDocument();
  });

  it("with absolute comparison, renders the expected variant, comparison, and user count", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableResults
            {...{ experiment }}
            branchComparison={BRANCH_COMPARISON.ABSOLUTE}
          />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );
    expect(screen.getByText("88.6%", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("198")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
    expect(
      screen.getAllByText("0.02 to 0.08 (baseline)", { exact: false }),
    ).toHaveLength(2);
    expect(screen.getByText("control")).toBeInTheDocument();
    expect(screen.getByText("treatment")).toBeInTheDocument();
  });

  it("renders correctly labelled result significance", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider>
          <TableResults
            {...{ experiment }}
            branchComparison={BRANCH_COMPARISON.ABSOLUTE}
          />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );
    expect(screen.getByTestId("positive-significance")).toBeInTheDocument();
    expect(screen.getByTestId("negative-significance")).toBeInTheDocument();
    expect(screen.queryAllByTestId("neutral-significance")).toHaveLength(2);
  });

  it("renders missing retention with warning", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider analysis={mockIncompleteAnalysis()}>
          <TableResults {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );

    const EXPECTED_TEXT = "2-Week Browser Retention is not available";
    expect(screen.getAllByText(EXPECTED_TEXT)).toHaveLength(2);
  });
});
