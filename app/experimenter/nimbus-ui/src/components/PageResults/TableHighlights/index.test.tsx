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
});
