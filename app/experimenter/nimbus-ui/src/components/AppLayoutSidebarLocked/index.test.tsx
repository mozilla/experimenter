/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import { render, screen } from "@testing-library/react";
import React from "react";
import { AppLayoutSidebarLocked, RESULTS_LOADING_TEXT } from ".";
import { BASE_PATH } from "../../lib/constants";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockAnalysis } from "../../lib/visualization/mocks";
import { AnalysisData } from "../../lib/visualization/types";
import { NimbusExperimentStatus } from "../../types/globalTypes";

const { mock } = mockExperimentQuery("my-special-slug/design");
const navLinkSelector = ".navbar a";

const Subject = ({
  status = NimbusExperimentStatus.COMPLETE,
  withAnalysis = false,
  analysisError,
  analysisLoadingInSidebar = false,
  primaryOutcomes = null,
  secondaryOutcomes = null,
}: RouteComponentProps & {
  status?: NimbusExperimentStatus;
  withAnalysis?: boolean;
  analysis?: AnalysisData;
  analysisError?: boolean;
  analysisLoadingInSidebar?: boolean;
  primaryOutcomes?: (string | null)[] | null;
  secondaryOutcomes?: (string | null)[] | null;
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
              metadata: mockAnalysis().metadata,
              other_metrics: mockAnalysis().other_metrics,
            }
          : undefined,
        primaryOutcomes,
        secondaryOutcomes,
      }}
    >
      <p data-testid="test-child">Hello, world!</p>
    </AppLayoutSidebarLocked>
  </RouterSlugProvider>
);

describe("AppLayoutSidebarLocked", () => {
  describe("navigation links", () => {
    it("when live, hides edit and review links, displays summary link and disabled results item", () => {
      render(<Subject status={NimbusExperimentStatus.LIVE} />);
      [
        "Overview",
        "Branches",
        "Metrics",
        "Audience",
        "Review & Launch",
      ].forEach((text) => {
        expect(
          screen.queryByText(text, { selector: navLinkSelector }),
        ).not.toBeInTheDocument();
      });

      const navSummary = screen.getByText("Summary", {
        selector: navLinkSelector,
      });
      expect(navSummary).toHaveAttribute(
        "href",
        `${BASE_PATH}/my-special-slug`,
      );

      screen.getByText("Experiment results not yet ready");
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
    it("when complete and has analysis results displays summary and results items", () => {
      render(<Subject withAnalysis />);

      for (const [label, path] of [
        ["Summary", ""],
        ["Results", "/results"],
      ]) {
        const link = screen.queryByText(label, { selector: navLinkSelector });
        expect(link).toHaveAttribute(
          "href",
          `${BASE_PATH}/my-special-slug${path}`,
        );
      }
    });

    it("shows correct sidebar items for 'other metrics'", () => {
      render(<Subject withAnalysis />);
      [
        "Monitoring",
        "Overview",
        "Results Summary",
        "Default Metrics",
        "Feature D Friendly Name",
      ].forEach((item) => {
        expect(screen.getByText(item)).toBeInTheDocument();
      });
    });

    it("when complete has expected results page items in side bar", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(
        <Subject
          primaryOutcomes={experiment.primaryOutcomes}
          secondaryOutcomes={experiment.secondaryOutcomes}
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
