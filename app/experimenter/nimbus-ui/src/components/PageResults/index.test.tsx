/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, render, waitFor } from "@testing-library/react";
import PageResults from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";
import fetchMock from "jest-fetch-mock";
import * as hooks from "../../hooks/useAnalysis";

const { mock } = mockExperimentQuery("demo-slug");

const Subject = () => (
  <RouterSlugProvider mocks={[mock]}>
    <PageResults />
  </RouterSlugProvider>
);

describe("PageResults", () => {
  beforeAll(() => {
    fetchMock.enableMocks();
  });

  afterAll(() => {
    fetchMock.disableMocks();
  });

  beforeEach(() => {
    fetchMock.resetMocks();
  });

  it("renders as expected", async () => {
    render(<Subject />);
    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
  });

  it("displays analysis data", async () => {
    fetchMock.mockResponseOnce(
      JSON.stringify({ burrito: "Nacho Cheese Doritos® Locos Tacos Supreme®" }),
    );

    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
      expect(screen.queryByTestId("analysis-data")).toBeInTheDocument();
    });
  });

  it("displays analysis load error", async () => {
    fetchMock.mockRejectOnce(new Error("Cheesy Gordita Crunch"));

    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
      expect(screen.queryByTestId("analysis-error")).toBeInTheDocument();
    });
  });

  it("displays analysis loading", async () => {
    // Can't wait for Experiment data to load and *not* analysis
    // data, so instead let's just mock the returned hook data
    (jest.spyOn(hooks, "useAnalysis") as jest.Mock).mockReturnValueOnce({
      loading: true,
    });

    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("analysis-loading")).toBeInTheDocument();
    });
  });
});
