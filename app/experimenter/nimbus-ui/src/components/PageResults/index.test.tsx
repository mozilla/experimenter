/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import { act } from "react-dom/test-utils";
import PageResults from ".";
import { getStatus as mockGetStatus } from "../../lib/experiment";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import {
  mockAnalysis,
  MOCK_METADATA_WITH_CONFIG,
  MOCK_UNAVAILABLE_ANALYSIS,
} from "../../lib/visualization/mocks";
import { AnalysisData } from "../../lib/visualization/types";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";

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
    expect(screen.queryByTestId("summary")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("table-highlights-overview"),
    ).toBeInTheDocument();
    // length of 2 due to two sets of tabs per table
    expect(screen.queryAllByTestId("table-highlights")).toHaveLength(2);
    expect(screen.queryAllByTestId("table-results")).toHaveLength(2);
    expect(screen.getAllByTestId("table-metric-secondary")).toHaveLength(4);
    expect(screen.queryByTestId("link-external-results")).toHaveAttribute(
      "href",
      "https://protosaur.dev/partybal/demo_slug.html",
    );
  });

  it("displays the external config alert when an override exists", async () => {
    mockExperiment = mockExperimentQuery("demo-slug").experiment;
    mockAnalysisData = mockAnalysis({ metadata: MOCK_METADATA_WITH_CONFIG });
    render(<Subject />);

    await screen.findByTestId("external-config-alert");
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

  it("redirects to the edit overview page if the experiment status is draft", async () => {
    mockExperiment = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    }).experiment;
    render(<Subject />);
    expect(redirectPath).toEqual("edit/overview");
  });

  it("redirects to the summary page if the visualization flag is set to false", async () => {
    mockAnalysisData = mockAnalysis({ show_analysis: false });
    mockExperiment = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.COMPLETE,
    }).experiment;
    render(<Subject />);
    expect(redirectPath).toEqual("");
  });

  it("redirects to the summary page if the visualization results are not ready", async () => {
    mockAnalysisData = MOCK_UNAVAILABLE_ANALYSIS;
    mockExperiment = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.COMPLETE,
    }).experiment;
    render(<Subject />);
    expect(redirectPath).toEqual("");
  });
});

it("displays grouped metrics via onClick", async () => {
  mockExperiment = mockExperimentQuery("demo-slug").experiment;
  mockAnalysisData = mockAnalysis();
  render(<Subject />);
  await waitFor(() => {
    expect(screen.queryByTestId("PageResults")).toBeInTheDocument();
  });

  await act(async () => {
    fireEvent.click(screen.getByText("Hide other metrics"));
  });
  expect(screen.getByText("Show other metrics")).toBeInTheDocument();
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
          refetch: () => Promise.resolve(),
        })}
      </div>
    );
  },
}));
