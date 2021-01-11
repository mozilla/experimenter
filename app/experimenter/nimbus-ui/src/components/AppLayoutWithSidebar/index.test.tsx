/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import AppLayoutWithSidebar, { RESULTS_LOADING_TEXT } from ".";
import { renderWithRouter, RouterSlugProvider } from "../../lib/test-utils";
import { BASE_PATH } from "../../lib/constants";
import { RouteComponentProps } from "@reach/router";
import App from "../App";
import {
  MockedCache,
  mockExperimentQuery,
  mockGetStatus,
} from "../../lib/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";

const { mock } = mockExperimentQuery("my-special-slug");

const Subject = ({
  status = NimbusExperimentStatus.DRAFT,
  withAnalysis = false,
  analysisError,
  review,
  analysisLoadingInSidebar = false,
}: RouteComponentProps & {
  status?: NimbusExperimentStatus;
  review?: {
    ready: boolean;
    invalidPages: string[];
  };
  withAnalysis?: boolean;
  analysisError?: boolean;
  analysisLoadingInSidebar?: boolean;
}) => (
  <RouterSlugProvider mocks={[mock]} path="/my-special-slug/edit">
    <AppLayoutWithSidebar
      {...{
        status: mockGetStatus(status),
        review,
        analysisLoadingInSidebar,
        analysisError: analysisError ? new Error("boop") : undefined,
        analysis: withAnalysis
          ? {
              show_analysis: true,
              daily: [],
              weekly: [],
              overall: {},
            }
          : undefined,
      }}
    >
      <p data-testid="test-child">Hello, world!</p>
    </AppLayoutWithSidebar>
  </RouterSlugProvider>
);

describe("AppLayoutWithSidebar", () => {
  it("renders app layout content with children", () => {
    render(<Subject />);
    expect(screen.getByTestId("AppLayoutWithSidebar")).toBeInTheDocument();
    expect(screen.getByTestId("test-child")).toBeInTheDocument();
  });

  describe("navigation links", () => {
    it("renders expected URLs", () => {
      render(<Subject />);
      expect(screen.getByTestId("nav-home")).toHaveAttribute("href", BASE_PATH);
      expect(screen.getByTestId("nav-edit-overview")).toHaveAttribute(
        "href",
        `${BASE_PATH}/my-special-slug/edit/overview`,
      );
      expect(screen.getByTestId("nav-edit-branches")).toHaveAttribute(
        "href",
        `${BASE_PATH}/my-special-slug/edit/branches`,
      );
      expect(screen.getByTestId("nav-edit-metrics")).toHaveAttribute(
        "href",
        `${BASE_PATH}/my-special-slug/edit/metrics`,
      );
      expect(screen.getByTestId("nav-edit-audience")).toHaveAttribute(
        "href",
        `${BASE_PATH}/my-special-slug/edit/audience`,
      );
      expect(screen.getByTestId("nav-request-review")).toHaveAttribute(
        "href",
        `${BASE_PATH}/my-special-slug/request-review`,
      );
    });

    it("renders expected active page class", async () => {
      function pushState(page: string) {
        window.history.pushState(
          {},
          "",
          `${BASE_PATH}/my-special-slug/${page}`,
        );
      }
      const {
        history: { navigate },
      } = renderWithRouter(
        <MockedCache mocks={[mock, mock, mock]}>
          <App basepath="/" />
        </MockedCache>,
        {
          route: `/my-special-slug/`,
        },
      );

      let overviewLink: HTMLElement, branchesLink: HTMLElement;

      pushState("edit/overview");
      await act(() => navigate("/my-special-slug/edit/overview"));
      await waitFor(() => {
        overviewLink = screen.getByTestId("nav-edit-overview");
        branchesLink = screen.getByTestId("nav-edit-branches");
      });
      expect(overviewLink!).toHaveClass("text-primary");
      expect(overviewLink!).not.toHaveClass("text-dark");
      expect(branchesLink!).toHaveClass("text-dark");
      expect(branchesLink!).not.toHaveClass("text-primary");

      pushState("edit/branches");
      await act(() => navigate("/my-special-slug/edit/branches"));
      await waitFor(() => {
        overviewLink = screen.getByTestId("nav-edit-overview");
        branchesLink = screen.getByTestId("nav-edit-branches");
      });
      expect(branchesLink!).toHaveClass("text-primary");
      expect(branchesLink!).not.toHaveClass("text-dark");
      expect(overviewLink!).toHaveClass("text-dark");
      expect(overviewLink!).not.toHaveClass("text-primary");
    });

    it("renders information about missing experiment details", async () => {
      const review = {
        ready: false,
        invalidPages: ["overview", "branches", "metrics", "audience"],
      };
      render(<Subject {...{ review }} />);

      expect(screen.queryByTestId("missing-details")).toBeInTheDocument();

      review.invalidPages.forEach((page) => {
        expect(
          screen.queryByTestId(`missing-detail-alert-${page}`),
        ).toBeInTheDocument();
        expect(
          screen.queryByTestId(`missing-detail-link-${page}`),
        ).toBeInTheDocument();
      });
    });

    it("renders the review & launch link when the experiment is ready for review", async () => {
      const review = {
        ready: true,
        invalidPages: [],
      };
      render(<Subject {...{ review }} />);

      expect(screen.queryByTestId("missing-details")).not.toBeInTheDocument();
      expect(screen.queryByTestId("nav-request-review")).toBeInTheDocument();
    });

    it("when in review, disables all edit page links", async () => {
      render(<Subject status={NimbusExperimentStatus.REVIEW} />);

      // In review these should all not be <a> tags, but instead <span>s
      ["overview", "branches", "metrics", "audience"].forEach((slug) => {
        expect(screen.getByTestId(`nav-edit-${slug}`).tagName).toEqual("SPAN");
      });
    });

    it("when live, hides edit and review links, displays design link and disabled results item", async () => {
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

    it("when accepted, displays design link and disabled results item", async () => {
      render(<Subject status={NimbusExperimentStatus.ACCEPTED} />);

      expect(screen.queryByTestId("show-no-results")).toBeInTheDocument();
      expect(screen.queryByTestId("show-no-results")).toHaveTextContent(
        "Waiting for experiment to launch",
      );
    });

    it("when complete and analysis results fetch errors", async () => {
      render(
        <Subject status={NimbusExperimentStatus.COMPLETE} analysisError />,
      );

      expect(screen.queryByTestId("show-no-results")).toBeInTheDocument();
      expect(screen.queryByTestId("show-no-results")).toHaveTextContent(
        "Could not get visualization data. Please contact data science",
      );
    });

    it("when complete and analysis is required in sidebar and loading", async () => {
      render(
        <Subject
          status={NimbusExperimentStatus.COMPLETE}
          analysisLoadingInSidebar
        />,
      );

      expect(screen.queryByTestId("show-no-results")).toBeInTheDocument();
      expect(screen.queryByTestId("show-no-results")).toHaveTextContent(
        RESULTS_LOADING_TEXT,
      );
    });

    it("when complete and has analysis results displays design and results items", async () => {
      render(<Subject status={NimbusExperimentStatus.COMPLETE} withAnalysis />);

      ["design", "results"].forEach((slug) => {
        expect(screen.queryByTestId(`nav-${slug}`)).toBeInTheDocument();
        expect(screen.queryByTestId(`nav-${slug}`)).toHaveAttribute(
          "href",
          `${BASE_PATH}/my-special-slug/${slug}`,
        );
      });
    });
  });
});
