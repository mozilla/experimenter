/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import { render, screen } from "@testing-library/react";
import React from "react";
import { AppLayoutSidebarLaunched, RESULTS_WAITING_FOR_LAUNCH_TEXT } from ".";
import { BASE_PATH } from "../../lib/constants";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import {
  mockAnalysis,
  MOCK_METADATA_WITH_CONFIG,
} from "../../lib/visualization/mocks";
import { AnalysisData } from "../../lib/visualization/types";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "../../types/globalTypes";

const { mock, experiment: defaultExperiment } = mockExperimentQuery(
  "my-special-slug/design",
);
const navLinkSelector = ".navbar a";

const Subject = ({
  status = NimbusExperimentStatusEnum.COMPLETE,
  publishStatus = NimbusExperimentPublishStatusEnum.IDLE,
  withAnalysis = false,
  analysisError,
  analysis,
  analysisRequired = true,
  experiment = defaultExperiment,
}: RouteComponentProps & {
  status?: NimbusExperimentStatusEnum;
  publishStatus?: NimbusExperimentPublishStatusEnum;
  withAnalysis?: boolean;
  analysis?: AnalysisData;
  analysisError?: boolean;
  analysisRequired?: boolean;
  experiment?: getExperiment_experimentBySlug;
}) => {
  const mockedAnalysis =
    analysis ||
    (withAnalysis
      ? {
          show_analysis: true,
          daily: [],
          weekly: {},
          overall: mockAnalysis().overall,
          errors: mockAnalysis().errors,
          metadata: mockAnalysis().metadata,
          other_metrics: mockAnalysis().other_metrics,
        }
      : undefined);
  return (
    <RouterSlugProvider mocks={[mock]} path="/my-special-slug/edit">
      <AppLayoutSidebarLaunched
        {...{
          status: mockGetStatus({ status, publishStatus }),
          analysisRequired,
          analysisError: analysisError ? new Error("boop") : undefined,
          analysis: mockedAnalysis,
          experiment,
          refetch: async () => {},
        }}
      >
        <p data-testid="test-child">Hello, world!</p>
      </AppLayoutSidebarLaunched>
    </RouterSlugProvider>
  );
};

describe("AppLayoutSidebarLaunched", () => {
  describe("navigation links", () => {
    it("when live, hides edit links, displays summary link and disabled results item", () => {
      render(<Subject status={NimbusExperimentStatusEnum.LIVE} />);
      ["Overview", "Branches", "Metrics", "Audience"].forEach((text) => {
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

      screen.getByText("Experiment analysis not ready yet");
    });

    it("when complete and analysis results fetch errors", () => {
      render(<Subject analysisError />);

      expect(screen.queryByTestId("show-no-results")).toBeInTheDocument();
      expect(screen.queryByTestId("show-no-results")).toHaveTextContent(
        "Could not get visualization data. Please contact data science",
      );
    });

    it("does not display waiting to launch message when pending end", () => {
      render(
        <Subject
          status={NimbusExperimentStatusEnum.COMPLETE}
          publishStatus={NimbusExperimentPublishStatusEnum.WAITING}
        />,
      );
      expect(
        screen.queryByText(RESULTS_WAITING_FOR_LAUNCH_TEXT),
      ).not.toBeInTheDocument();
    });

    it("when analysis is skipped", () => {
      render(
        <Subject
          analysis={{
            show_analysis: true,
            daily: null,
            weekly: null,
            overall: null,
            errors: null,
            metadata: MOCK_METADATA_WITH_CONFIG,
          }}
        />,
      );
      expect(screen.queryByTestId("show-no-results")).toHaveTextContent(
        "Experiment analysis was skipped",
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
      render(<Subject withAnalysis {...{ experiment }} />);
      [
        "Overview",
        "Results Summary",
        "Primary Outcomes",
        "Picture-in-Picture",
        "Secondary Outcomes",
        "Feature B",
      ].forEach((item) => {
        expect(screen.getByText(item)).toBeInTheDocument();
      });
    });

    it("when complete and page does not require full analysis data, has expected results page items in side bar", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(
        <Subject withAnalysis analysisRequired={false} {...{ experiment }} />,
      );
      [
        "Overview",
        "Results Summary",
        "Primary Outcomes",
        "Picture-in-Picture",
        "Secondary Outcomes",
        "Feature B",
      ].forEach((item) => {
        expect(screen.getByText(item)).toBeInTheDocument();
      });
    });
  });
});
