/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableHighlights from ".";
import {
  mockExperimentQuery,
  MockResultsContextProvider,
} from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import {
  mockAnalysis,
  MOCK_METADATA_NO_REF_BRANCH,
} from "../../../lib/visualization/mocks";

const { mock, experiment } = mockExperimentQuery("demo-slug");

describe("TableHighlights", () => {
  it("recieves correct controlBranchName from Context when metadata contains `reference_branch`", async () => {
    const metadata = {
      ...MOCK_METADATA_NO_REF_BRANCH,
      reference_branch: "treatment",
    };
    const analysis = mockAnalysis({ metadata });
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider {...{ analysis }}>
          <TableHighlights {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );

    // branches get sorted with the control branch displayed first
    await screen.findByText("treatment", {
      selector: "table tr:first-of-type",
    });
  });

  it("sets controlBranchName in Context correctly when metadata does not contain `reference_branch`", async () => {
    const analysis = mockAnalysis({ metadata: MOCK_METADATA_NO_REF_BRANCH });
    render(
      <RouterSlugProvider mocks={[mock]}>
        <MockResultsContextProvider {...{ analysis }}>
          <TableHighlights {...{ experiment }} />
        </MockResultsContextProvider>
      </RouterSlugProvider>,
    );

    // branches get sorted with the control branch displayed first
    await screen.findByText("control", { selector: "table tr:first-of-type" });
  });
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
});
