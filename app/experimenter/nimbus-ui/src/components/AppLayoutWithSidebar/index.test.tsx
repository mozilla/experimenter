/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { act, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { BASE_PATH, SERVER_ERRORS } from "../../lib/constants";
import { MockedCache, mockExperimentQuery } from "../../lib/mocks";
import { renderWithRouter } from "../../lib/test-utils";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import App from "../App";
import { Subject } from "./mocks";

const assertDisabledNav = () => {
  for (const slug of ["overview", "branches", "metrics", "audience"]) {
    expect(screen.getByTestId(`nav-edit-${slug}`).tagName).toEqual("SPAN");
  }
};

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
      const { mock } = mockExperimentQuery("my-special-slug");
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
      render(
        <Subject
          experiment={{
            readyForReview: {
              ready: false,
              message: {
                channel: [SERVER_ERRORS.EMPTY_LIST],
              },
            },
          }}
        />,
      );

      await screen.findByText(/Missing details in:/);
    });

    it("when in preview, disables all edit page links", async () => {
      render(
        <Subject experiment={{ status: NimbusExperimentStatus.PREVIEW }} />,
      );

      // In preview these should all not be <a> tags, but instead <span>s
      ["overview", "branches", "metrics", "audience"].forEach((slug) => {
        expect(screen.getByTestId(`nav-edit-${slug}`).tagName).toEqual("SPAN");
      });
    });

    it("when in draft and publish status review, disables all edit page links", async () => {
      render(
        <Subject
          experiment={{ publishStatus: NimbusExperimentPublishStatus.REVIEW }}
        />,
      );
      assertDisabledNav();
    });

    it("when in draft and publish status approved, disables all edit page links", async () => {
      render(
        <Subject
          experiment={{ publishStatus: NimbusExperimentPublishStatus.APPROVED }}
        />,
      );
      assertDisabledNav();
    });

    it("when in in draft and publish status waiting, disables all edit page links", async () => {
      render(
        <Subject
          experiment={{ publishStatus: NimbusExperimentPublishStatus.WAITING }}
        />,
      );
      assertDisabledNav();
    });
  });
});
