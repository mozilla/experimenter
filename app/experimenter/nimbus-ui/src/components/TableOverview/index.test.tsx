/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import TableOverview from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { mockAnalysis } from "../../lib/visualization/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";

const { mock, data } = mockExperimentQuery("demo-slug");

describe("TableOverview", () => {
  it("has the correct headings", async () => {
    const EXPECTED_HEADINGS = ["Targeting", "Probe Sets", "Owner"];

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableOverview experiment={data!} results={mockAnalysis().overall} />
      </RouterSlugProvider>,
    );

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("has the expected targeting", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableOverview experiment={data!} results={mockAnalysis().overall} />
      </RouterSlugProvider>,
    );

    expect(screen.getByText("Firefox 80+")).toBeInTheDocument();
    expect(
      screen.getByText("Desktop Nightly, Desktop Beta"),
    ).toBeInTheDocument();
    expect(screen.getByText("Us Only")).toBeInTheDocument();
  });

  it("has the expected probe sets", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableOverview experiment={data!} results={mockAnalysis().overall} />
      </RouterSlugProvider>,
    );

    expect(screen.getByText("Picture-in-Picture")).toBeInTheDocument();
  });

  it("has the experiment owner", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableOverview experiment={data!} results={mockAnalysis().overall} />
      </RouterSlugProvider>,
    );
    expect(screen.getByText("example@mozilla.com")).toBeInTheDocument();
  });
});
