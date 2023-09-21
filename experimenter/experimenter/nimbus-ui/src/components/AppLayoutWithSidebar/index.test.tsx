/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import { Subject } from "src/components/AppLayoutWithSidebar/mocks";
import { BASE_PATH, SERVER_ERRORS } from "src/lib/constants";

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
      expect(
        screen.getByTestId("history-page-my-special-slug"),
      ).toHaveAttribute("href", `/history/my-special-slug`);
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
              warnings: {},
            },
          }}
        />,
      );

      await screen.findByText(/Missing details in:/);
    });

    it("when canEdit false, disables all edit page links", async () => {
      render(<Subject experiment={{ canEdit: false }} />);

      // In preview these should all not be <a> tags, but instead <span>s
      ["overview", "branches", "metrics", "audience"].forEach((slug) => {
        expect(screen.getByTestId(`nav-edit-${slug}`).tagName).toEqual("SPAN");
      });
    });
  });
});
