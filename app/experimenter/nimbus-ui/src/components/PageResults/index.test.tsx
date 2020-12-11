/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, render, waitFor } from "@testing-library/react";
import PageResults from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";
import { mockAnalysis } from "../../lib/visualization/mocks";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import { AnalysisData } from "../../lib/visualization/types";

const Subject = () => (
  <RouterSlugProvider>
    <PageResults />
  </RouterSlugProvider>
);

let mockAnalysisData: AnalysisData | undefined = mockAnalysis();

describe("PageResults", () => {
  it("renders as expected", async () => {
    render(<Subject />);
    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
  });

  it("fetches analysis data and displays expected tables when analysis is ready", async () => {
    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("table-summary")).not.toBeInTheDocument();
    expect(screen.queryByTestId("table-highlights")).toBeInTheDocument();
    expect(screen.queryByTestId("table-overview")).toBeInTheDocument();
    expect(screen.queryByTestId("table-results")).toBeInTheDocument();
    expect(screen.queryByTestId("table-metric-primary")).toBeInTheDocument();
    expect(screen.getAllByTestId("table-metric-secondary")).toHaveLength(2);
    expect(screen.queryByTestId("link-external-results")).toHaveAttribute(
      "href",
      "https://protosaur.dev/partybal/demo_slug.html",
    );
  });

  it("displays the monitoring dashboard link", async () => {
    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("link-monitoring-dashboard")).toHaveAttribute(
        "href",
        expect.stringContaining("https://grafana.telemetry.mozilla.org"),
      );
    });
  });

  it("fetches analysis data and displays as expected when analysis is not ready", async () => {
    mockAnalysisData!.show_analysis = false;

    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("analysis-unavailable")).toBeInTheDocument();
    expect(screen.queryByTestId("summary")).toBeInTheDocument();
  });

  it("displays analysis error when analysis fetch error occurs", async () => {
    mockAnalysisData = undefined;

    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("analysis-error")).toBeInTheDocument();
  });
});

// Mocking form component because validation is exercised in its own tests.
jest.mock("../AppLayoutWithExperiment", () => ({
  __esModule: true,
  default: (props: React.ComponentProps<typeof AppLayoutWithExperiment>) => (
    <div data-testid="PageResults">
      {props.children({
        experiment: mockExperimentQuery("demo-slug").experiment,
        analysis: mockAnalysisData,
        review: {
          isMissingField: () => false,
          refetch: () => {},
        },
      })}
    </div>
  ),
}));
