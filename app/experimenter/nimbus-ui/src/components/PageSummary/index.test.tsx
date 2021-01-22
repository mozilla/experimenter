/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen, waitFor } from "@testing-library/react";
import React from "react";
import PageSummary from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";

const { mock } = mockExperimentQuery("demo-slug");

describe("PageSummary", () => {
  it("renders as expected", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <PageSummary />
      </RouterSlugProvider>,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("PageSummary")).toBeInTheDocument();
    });

    // uses correct AppLayout
    expect(screen.queryByTestId("nav-sidebar")).not.toBeInTheDocument();
    expect(screen.queryByTestId("header-experiment")).toBeInTheDocument();
    expect(screen.queryByTestId("summary-timeline")).toBeInTheDocument();
    expect(screen.queryByTestId("table-summary")).toBeInTheDocument();
  });
});
