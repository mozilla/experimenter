/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen } from "@testing-library/react";
import AppLayoutWithSidebar from ".";
import { renderWithRouter } from "../../lib/helpers";
import { BASE_PATH } from "../../lib/constants";
import App from "../App";
import { RouteComponentProps, Router, useLocation } from "@reach/router";
import PageEditOverview from "../PageEditOverview";

describe("PageNew", () => {
  it("renders app layout content with children", () => {
    renderWithRouter(
      <AppLayoutWithSidebar>
        <p data-testid="test-child">Hello, world!</p>
      </AppLayoutWithSidebar>,
    );
    expect(screen.getByTestId("AppLayoutWithSidebar")).toBeInTheDocument();
    expect(screen.getByTestId("test-child")).toBeInTheDocument();
  });

  describe("navigation links", () => {
    const SidebarRoot = (props: RouteComponentProps) => (
      <AppLayoutWithSidebar>
        <p>Hello, world!</p>
      </AppLayoutWithSidebar>
    );

    it("renders expected URLs", () => {
      renderWithRouter(
        <Router>
          <SidebarRoot path="/:slug" />
        </Router>,
        { route: `/my-special-slug` },
      );
      expect(screen.getByTestId("nav-home")).toHaveAttribute("href", BASE_PATH);
      expect(screen.getByTestId("nav-edit-overview")).toHaveAttribute(
        "href",
        `${BASE_PATH}/my-special-slug/edit/overview`,
      );
      expect(screen.getByTestId("nav-edit-branches")).toHaveAttribute(
        "href",
        `${BASE_PATH}/my-special-slug/edit/branches`,
      );
      expect(screen.getByTestId("nav-request-review")).toHaveAttribute(
        "href",
        `${BASE_PATH}/my-special-slug/request-review`,
      );
    });
  });
});
