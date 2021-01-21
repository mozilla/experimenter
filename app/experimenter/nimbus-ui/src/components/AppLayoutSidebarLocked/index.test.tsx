/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import { RESULTS_LOADING_TEXT, AppLayoutSidebarLocked } from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { BASE_PATH } from "../../lib/constants";
import { RouteComponentProps } from "@reach/router";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { mockAnalysis } from "../../lib/visualization/mocks";
import {
  getExperiment_experimentBySlug_primaryProbeSets,
  getExperiment_experimentBySlug_secondaryProbeSets,
} from "../../types/getExperiment";
import { AnalysisData } from "../../lib/visualization/types";

const { mock } = mockExperimentQuery("my-special-slug/design");

const Subject = ({
  status = NimbusExperimentStatus.COMPLETE,
  withAnalysis = false,
  analysisError,
  analysisLoadingInSidebar = false,
  primaryProbeSets = null,
  secondaryProbeSets = null,
}: RouteComponentProps & {
  status?: NimbusExperimentStatus;
  withAnalysis?: boolean;
  analysis?: AnalysisData;
  analysisError?: boolean;
  analysisLoadingInSidebar?: boolean;
  primaryProbeSets?:
    | (getExperiment_experimentBySlug_primaryProbeSets | null)[]
    | null;
  secondaryProbeSets?:
    | (getExperiment_experimentBySlug_secondaryProbeSets | null)[]
    | null;
}) => (
  <RouterSlugProvider mocks={[mock]} path="/my-special-slug/edit">
    <AppLayoutSidebarLocked
      {...{
        status: mockGetStatus(status),
        analysisLoadingInSidebar,
        analysisError: analysisError ? new Error("boop") : undefined,
        analysis: withAnalysis
          ? {
              show_analysis: true,
              daily: [],
              weekly: {},
              overall: mockAnalysis().overall,
              other_metrics: mockAnalysis().other_metrics,
            }
          : undefined,
        primaryProbeSets,
        secondaryProbeSets,
      }}
    >
      <p data-testid="test-child">Hello, world!</p>
    </AppLayoutSidebarLocked>
  </RouterSlugProvider>
);

describe("AppLayoutSidebarLocked", () => {
  describe("navigation links", () => {
    it("when live, hides edit and review links, displays design link and disabled results item", () => {
      render(<Subject status={NimbusExperimentStatus.LIVE} />);
      [
        "edit-overview",
        "edit-branches",
        "edit-metrics",
        "edit-audience",
        "edit-request-review",
      ].forEach((slug) => {
        expect(screen.queryByTestId(`nav-${slug}`)).not.toBeInTheDocument();
      });

      expect(screen.queryByTestId("nav-design")).toBeInTheDocument();
      expect(screen.queryByTestId("nav-design")).toHaveAttribute(
        "href",
        `${BASE_PATH}/my-special-slug/design`,
      );
      expect(screen.queryByTestId("show-no-results")).toBeInTheDocument();
      expect(screen.queryByTestId("show-no-results")).toHaveTextContent(
        "Experiment results not yet ready",
      );
    });

    it("when accepted, displays design link and disabled results item", () => {
      render(<Subject status={NimbusExperimentStatus.ACCEPTED} />);

      expect(screen.queryByTestId("show-no-results")).toBeInTheDocument();
      expect(screen.queryByTestId("show-no-results")).toHaveTextContent(
        "Waiting for experiment to launch",
      );
    });

    it("when complete and analysis results fetch errors", () => {
      render(<Subject analysisError />);

      expect(screen.queryByTestId("show-no-results")).toBeInTheDocument();
      expect(screen.queryByTestId("show-no-results")).toHaveTextContent(
        "Could not get visualization data. Please contact data science",
      );
    });

    it("when complete and analysis is required in sidebar and loading", () => {
      render(<Subject analysisLoadingInSidebar />);

      expect(screen.queryByTestId("show-no-results")).toBeInTheDocument();
      expect(screen.queryByTestId("show-no-results")).toHaveTextContent(
        RESULTS_LOADING_TEXT,
      );
    });

    it("when complete and has analysis results displays design and results items", () => {
      render(<Subject withAnalysis />);

      ["design", "results"].forEach((slug) => {
        expect(screen.queryByTestId(`nav-${slug}`)).toBeInTheDocument();
        expect(screen.queryByTestId(`nav-${slug}`)).toHaveAttribute(
          "href",
          `${BASE_PATH}/my-special-slug/${slug}`,
        );
      });
    });

    it("shows correct sidebar items for 'other metrics'", () => {
      render(<Subject withAnalysis />);
      [
        "Monitoring",
        "Overview",
        "Results Summary",
        "Default Metrics",
        "Feature D",
      ].forEach((item) => {
        expect(screen.getByText(item)).toBeInTheDocument();
      });
    });

    it("when complete has expected results page items in side bar", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(
        <Subject
          primaryProbeSets={experiment.primaryProbeSets}
          secondaryProbeSets={experiment.secondaryProbeSets}
          withAnalysis
        />,
      );
      [
        "Monitoring",
        "Overview",
        "Results Summary",
        "Primary Metrics",
        "Picture-in-Picture",
        "Secondary Metrics",
        "Feature B",
      ].forEach((item) => {
        expect(screen.getByText(item)).toBeInTheDocument();
      });
    });
  });
});
