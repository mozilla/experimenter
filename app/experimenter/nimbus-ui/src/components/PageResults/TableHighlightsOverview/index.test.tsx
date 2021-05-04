/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableHighlightsOverview from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";

const { mock, experiment } = mockExperimentQuery("demo-slug");

describe("TableHighlightsOverview", () => {
  it("has the correct headings", async () => {
    const EXPECTED_HEADINGS = ["Targeting", "Outcomes", "Owner"];

    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableHighlightsOverview {...{ experiment }} />
      </RouterSlugProvider>,
    );

    EXPECTED_HEADINGS.forEach((heading) => {
      expect(screen.getByText(heading)).toBeInTheDocument();
    });
  });

  it("has the expected targeting", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableHighlightsOverview {...{ experiment }} />
      </RouterSlugProvider>,
    );

    expect(screen.getByText("Firefox 80+")).toBeInTheDocument();
    expect(screen.getByText("Desktop Nightly")).toBeInTheDocument();
    expect(screen.getByText("Us Only")).toBeInTheDocument();
  });

  it("has the expected outcomes", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableHighlightsOverview {...{ experiment }} />
      </RouterSlugProvider>,
    );

    expect(screen.getByText("Picture-in-Picture")).toBeInTheDocument();
  });

  it("has the experiment owner", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <TableHighlightsOverview {...{ experiment }} />
      </RouterSlugProvider>,
    );
    expect(screen.getByText("example@mozilla.com")).toBeInTheDocument();
  });
});
