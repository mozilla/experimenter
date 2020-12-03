/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, render, waitFor, fireEvent } from "@testing-library/react";
import PageEditMetrics from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";

const { mock } = mockExperimentQuery("demo-slug");

describe("PageEditMetrics", () => {
  it("renders as expected", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <PageEditMetrics />
      </RouterSlugProvider>,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("PageEditMetrics")).toBeInTheDocument();
    });
  });

  it("does nothing on Save", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <PageEditMetrics />
      </RouterSlugProvider>,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("PageEditMetrics")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Save"));
  });

  it("does nothing on Next", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <PageEditMetrics />
      </RouterSlugProvider>,
    );
    await waitFor(() => {
      expect(screen.queryByTestId("PageEditMetrics")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Next"));
  });
});
