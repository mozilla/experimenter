/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, waitFor, render } from "@testing-library/react";
import PageEditBranches from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";

const { mock } = mockExperimentQuery("demo-slug");
const { mock: notFoundMock } = mockExperimentQuery("demo-slug", null);

describe("PageEditBranches", () => {
  it("renders as expected with experiment data", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <PageEditBranches />
      </RouterSlugProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("PageEditBranches")).toBeInTheDocument();
      expect(screen.getByTestId("header-experiment")).toBeInTheDocument();
    });
  });

  it("renders not found screen", async () => {
    render(
      <RouterSlugProvider mocks={[notFoundMock]}>
        <PageEditBranches />
      </RouterSlugProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("not-found")).toBeInTheDocument();
    });
  });

  it("renders loading screen", () => {
    render(
      <RouterSlugProvider>
        <PageEditBranches />
      </RouterSlugProvider>,
    );

    expect(screen.getByTestId("page-loading")).toBeInTheDocument();
  });
});
