/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { ReactNode } from "react";
import { screen, waitFor } from "@testing-library/react";
import { renderWithRouter } from "../../lib/helpers";
import App from ".";

describe("App", () => {
  it("routes to PageHome page", () => {
    renderWithRouter(<App basepath="/" />);
    expect(screen.getByTestId("PageHome")).toBeInTheDocument();
  });

  it("routes to PageNew page", () => {
    renderWithRouter(<App basepath="/foo/bar" />, {
      route: "/foo/bar/new",
    });
    expect(screen.getByTestId("PageNew")).toBeInTheDocument();
  });

  describe(":slug routes", () => {
    it("redirects from ':slug/edit' to ':slug/edit/overview'", async () => {
      const {
        history: { navigate },
      } = renderWithRouter(<App basepath="/" />, {
        route: `/my-special-slug/`,
      });

      await navigate("/my-special-slug/edit");
      // waitFor the redirect
      await waitFor(() => {
        expect(screen.getByTestId("PageEditOverview")).toBeInTheDocument();
      });
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
