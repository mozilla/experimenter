/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import { render, screen } from "@testing-library/react";
import React from "react";
import {
  AppLayoutSidebarLaunched,
  RESULTS_WAITING_FOR_LAUNCH_TEXT,
} from "src/components/AppLayoutSidebarLaunched";
import { BASE_PATH } from "src/lib/constants";
import { mockExperimentQuery, mockGetStatus } from "src/lib/mocks";
import { RouterSlugProvider } from "src/lib/test-utils";
import {
  mockAnalysis,
  MOCK_METADATA_WITH_CONFIG,
} from "src/lib/visualization/mocks";
import { AnalysisData } from "src/lib/visualization/types";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "src/types/globalTypes";

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
          daily: { enrollments: { all: [] } },
          weekly: { enrollments: { all: {} } },
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
      const { experiment } = mockExperimentQuery("my-special-slug", {
        showResultsUrl: true,
      });
      render(<Subject withAnalysis {...{ experiment }} />);

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
      const { experiment } = mockExperimentQuery("demo-slug", {
        showResultsUrl: true,
      });
      render(<Subject withAnalysis {...{ experiment }} />);
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
      const { experiment } = mockExperimentQuery("demo-slug", {
        showResultsUrl: true,
      });
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
      const { experiment } = mockExperimentQuery("demo-slug", {
        showResultsUrl: true,
      });
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

    it("when rollout show audience page", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        isRollout: true,
      });
      render(<Subject withAnalysis {...{ experiment }} />);

      expect(screen.queryByText("Summary")).toBeInTheDocument();
      expect(screen.queryByText("Audience")).toBeInTheDocument();
    });

    it("when experiment do not show audience page", () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        isRollout: false,
      });
      render(<Subject withAnalysis {...{ experiment }} />);

      expect(screen.queryByText("Summary")).toBeInTheDocument();
      expect(screen.queryByText("Audience")).not.toBeInTheDocument();
    });

    it("when a completed rollout do not show audience page", () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      experiment.isRollout = true;
      experiment.status = NimbusExperimentStatusEnum.COMPLETE;
      render(<Subject withAnalysis {...{ experiment }} />);

      expect(screen.queryByText("Summary")).toBeInTheDocument();
      expect(screen.queryByText("Audience")).not.toBeInTheDocument();
    });
  });
});
