/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableResults from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import {
  mockAnalysis,
  mockIncompleteAnalysis,
} from "../../../lib/visualization/mocks";
import { getSortedBranches } from "../../../lib/visualization/utils";

const { mock, experiment } = mockExperimentQuery("demo-slug");
const results = mockAnalysis();
const sortedBranches = getSortedBranches(results);

describe("TableResults", () => {
  it("renders correct headings", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableResults {...{ experiment, results, sortedBranches }} />
      </RouterSlugProvider>,
    );
    const EXPECTED_HEADINGS = [
      "Picture-in-Picture Conversion",
      "2-Week Browser Retention",
      "Daily Mean Searches Per User",
      "Overall Mean Days of Use Per User",
      "Total Users",
    ];

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("renders the expected variant and user count", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableResults {...{ experiment, results, sortedBranches }} />
      </RouterSlugProvider>,
    );

    expect(screen.getByText("control")).toBeInTheDocument();
    expect(screen.getByText("treatment")).toBeInTheDocument();
    expect(screen.getByText("198")).toBeInTheDocument();
  });

  it("renders correctly labelled result significance", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableResults {...{ experiment, results, sortedBranches }} />
      </RouterSlugProvider>,
    );

    expect(screen.getByTestId("positive-significance")).toBeInTheDocument();
    expect(screen.getByTestId("negative-significance")).toBeInTheDocument();
    expect(screen.queryAllByTestId("neutral-significance")).toHaveLength(2);
  });

  it("renders missing retention with warning", () => {
    const results = mockIncompleteAnalysis();
    const sortedBranches = getSortedBranches(results);

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableResults {...{ experiment, results, sortedBranches }} />
      </RouterSlugProvider>,
    );

    const EXPECTED_TEXT = "2-Week Browser Retention is not available";
    expect(screen.getAllByText(EXPECTED_TEXT)).toHaveLength(2);
  });
});
