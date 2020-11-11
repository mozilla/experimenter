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
import { mockAnalysis } from "../../lib/visualization/mocks";

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

  it("fetches analysis data and displays expected tables when analysis is ready", async () => {
    fetchMock.mockResponseOnce(JSON.stringify(mockAnalysis()));

    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("table-summary")).not.toBeInTheDocument();
    expect(screen.queryByTestId("table-highlights")).toBeInTheDocument();
    expect(screen.queryByTestId("table-overview")).toBeInTheDocument();
    expect(screen.queryByTestId("table-results")).toBeInTheDocument();
    expect(screen.queryByTestId("table-metric-primary")).toBeInTheDocument();
    expect(screen.queryByTestId("table-metric-secondary")).toBeInTheDocument();
  });

  it("displays the monitoring dashboard link", async () => {
    fetchMock.mockResponseOnce(JSON.stringify(mockAnalysis()));

    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("link-monitoring-dashboard")).toHaveAttribute(
        "href",
        "https://grafana.telemetry.mozilla.org/d/XspgvdxZz/experiment-enrollment?orgId=1&var-experiment_id=demo-slug",
      );
    });
  });

  it("displays analysis load error", async () => {
    fetchMock.mockRejectOnce(new Error("Cheesy Gordita Crunch"));

    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("analysis-error")).toBeInTheDocument();
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

  it("fetches analysis data and displays as expected when analysis is not ready", async () => {
    fetchMock.mockResponseOnce(
      JSON.stringify(mockAnalysis({ show_analysis: false })),
    );

    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("table-summary")).toBeInTheDocument();
    expect(screen.queryByTestId("link-external-results")).toHaveAttribute(
      "href",
      "https://protosaur.dev/partybal/demo_slug.html",
    );
  });
});
