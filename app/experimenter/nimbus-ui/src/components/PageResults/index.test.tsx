/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, render, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import PageResults from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";
import { mockAnalysis } from "../../lib/visualization/mocks";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import { AnalysisData } from "../../lib/visualization/types";
import { getStatus as mockGetStatus } from "../../lib/experiment";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

const Subject = () => (
  <RouterSlugProvider>
    <PageResults />
  </RouterSlugProvider>
);

let mockExperiment: getExperiment_experimentBySlug;
let mockAnalysisData: AnalysisData | undefined;
let redirectPath: string | void;

describe("PageResults", () => {
  beforeAll(() => {
    fetchMock.enableMocks();
  });

  afterAll(() => {
    fetchMock.disableMocks();
  });

  it("renders as expected", async () => {
    mockExperiment = mockExperimentQuery("demo-slug").experiment;
    render(<Subject />);
    await waitFor(() => {
      expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
    });
  });

  it("fetches analysis data and displays expected tables when analysis is ready", async () => {
    mockExperiment = mockExperimentQuery("demo-slug").experiment;
    mockAnalysisData = mockAnalysis();
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
    mockExperiment = mockExperimentQuery("demo-slug").experiment;
    render(<Subject />);

    await waitFor(() => {
      expect(screen.queryByTestId("link-monitoring-dashboard")).toHaveAttribute(
        "href",
        expect.stringContaining("https://grafana.telemetry.mozilla.org"),
      );
    });
  });

  it("fetches analysis data and displays as expected when analysis is not ready", async () => {
    mockAnalysisData = mockAnalysis({ show_analysis: false });

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

  it("redirects to the edit overview page if the experiment status is draft", async () => {
    mockExperiment = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    }).experiment;
    render(<Subject />);
    expect(redirectPath).toEqual("edit/overview");
  });

  it("redirects to the edit overview page if the experiment status is review", async () => {
    mockExperiment = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    }).experiment;
    render(<Subject />);
    expect(redirectPath).toEqual("edit/overview");
  });

  it("redirects to the design page if the analysis results are not ready", async () => {
    mockAnalysisData = mockAnalysis({ show_analysis: false });
    mockExperiment = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.COMPLETE,
    }).experiment;
    render(<Subject />);
    expect(redirectPath).toEqual("design");
  });
});

// Mocking form component because validation is exercised in its own tests.
jest.mock("../AppLayoutWithExperiment", () => ({
  __esModule: true,
  default: (props: React.ComponentProps<typeof AppLayoutWithExperiment>) => {
    const experiment = mockExperiment;
    const analysis = mockAnalysisData;

    redirectPath = props.redirect!({
      status: mockGetStatus(experiment),
      analysis: mockAnalysisData,
    });

    return (
      <div data-testid="PageResults">
        {props.children({
          experiment,
          analysis,
          review: {
            isMissingField: () => false,
            refetch: () => {},
            ready: true,
            invalidPages: [],
            missingFields: [],
          },
        })}
      </div>
    );
  },
}));
