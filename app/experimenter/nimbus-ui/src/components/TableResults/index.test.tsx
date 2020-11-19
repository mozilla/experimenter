/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import TableResults from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";
import { mockAnalysis } from "../../lib/visualization/mocks";

const { mock, data } = mockExperimentQuery("demo-slug");

describe("TableResults", () => {
  it("renders correct headings", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableResults
          primaryProbeSets={data!.primaryProbeSets!}
          results={mockAnalysis().overall}
        />
      </RouterSlugProvider>,
    );
    const EXPECTED_HEADINGS = [
      "Picture-in-Picture Conversion",
      "2-Week Browser Retention",
      "Daily Mean Searches Per User",
      "Total Users",
    ];

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("renders the expected variant and user count", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableResults
          primaryProbeSets={data!.primaryProbeSets!}
          results={mockAnalysis().overall}
        />
      </RouterSlugProvider>,
    );

    expect(screen.getByText("control")).toBeInTheDocument();
    expect(screen.getByText("treatment")).toBeInTheDocument();
    expect(screen.getByText("198")).toBeInTheDocument();
  });

  it("renders correctly labelled result significance", () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableResults
          primaryProbeSets={data!.primaryProbeSets!}
          results={mockAnalysis().overall}
        />
      </RouterSlugProvider>,
    );

    expect(screen.getByTestId("positive-significance")).toBeInTheDocument();
    expect(screen.getByTestId("negative-significance")).toBeInTheDocument();
    expect(screen.getByTestId("neutral-significance")).toBeInTheDocument();
  });
});
