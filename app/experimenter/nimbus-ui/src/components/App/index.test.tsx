/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { ReactNode } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import {
  createMemorySource,
  createHistory,
  LocationProvider,
  Router,
  Redirect,
} from "@reach/router";
import { renderWithRouter } from "../../lib/helpers";
import App from ".";
import PageEditOverview from "../PageEditOverview";
import PageEditBranches from "../PageEditBranches";

describe("App", () => {
  const Subject = ({ basepath = "/", path = "/" }) => {
    let source = createMemorySource(path);
    let history = createHistory(source);

    return (
      <LocationProvider {...{ history }}>
        <App {...{ basepath }} />
      </LocationProvider>
    );
  };

  it("routes to PageHome page", () => {
    render(<Subject path="/" />);
    expect(screen.getByTestId("PageHome")).toBeInTheDocument();
  });

  it("routes to PageNew page", () => {
    render(<Subject basepath="/foo/bar" path="/foo/bar/new" />);
    expect(screen.getByTestId("PageNew")).toBeInTheDocument();
  });

  describe(":slug routes", () => {
    const Root = (props: any) => <>{props.children}</>;
    const Routes = () => (
      <Router>
        <Root path="/:slug/edit">
          <Redirect from="/" to="overview" noThrow />
          <PageEditOverview path="overview" />
          <PageEditBranches path="branches" />
        </Root>
      </Router>
    );

    it("redirects from ':slug/edit' to ':slug/edit/overview'", async () => {
      const {
        history: { navigate },
      } = renderWithRouter(<Routes />, {
        route: `/my-special-slug/`,
      });

      await navigate("/my-special-slug/edit");
      // we have to waitFor the redirect
      await waitFor(() => {
        expect(screen.getByTestId("PageEditOverview")).toBeInTheDocument();
      });
    });

    it("renders expected active page class in nav", async () => {
      const {
        history: { navigate },
      } = renderWithRouter(<Routes />, {
        route: `/my-special-slug/`,
      });
      // this fails because location.pathname is still set to "/"
      // and `isCurrent` checks location.pathname against the href
      await navigate("/my-special-slug/edit/overview");
      const overviewLink = screen.getByTestId("nav-edit-overview");
      const branchesLink = screen.getByTestId("nav-edit-branches");
      expect(overviewLink).toHaveClass("text-primary");
      expect(branchesLink).not.toHaveClass("text-primary");
      await navigate("/my-special-slug/edit/branches");
      expect(branchesLink).toHaveClass("text-primary");
      expect(overviewLink).not.toHaveClass("text-primary");
    });
  });
});

jest.mock("../PageHome", () => ({
  __esModule: true,
  default: mockComponent("PageHome"),
}));

jest.mock("../PageNew", () => ({
  __esModule: true,
  default: mockComponent("PageNew"),
}));

function mockComponent(testid: string) {
  return (props: { children: ReactNode }) => (
    <div data-testid={testid}>{props.children}</div>
  );
}
