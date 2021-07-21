/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import * as apollo from "@apollo/client";
import { screen, waitFor } from "@testing-library/react";
import React, { ReactNode } from "react";
import App from ".";
import { MockedCache, mockExperimentQuery } from "../../lib/mocks";
import { renderWithRouter } from "../../lib/test-utils";

const { mock } = mockExperimentQuery("my-special-slug");

describe("App", () => {
  it("displays loading when config is loading", () => {
    (jest.spyOn(apollo, "useQuery") as jest.Mock).mockReturnValueOnce({
      loading: true,
    });

    renderWithRouter(
      <MockedCache mocks={[]}>
        <App basepath="/" />
      </MockedCache>,
    );
    expect(screen.getByTestId("page-loading")).toBeInTheDocument();
  });

  it("renders the error alert when an error occurs querying the config", () => {
    const error = new Error("boop");

    (jest.spyOn(apollo, "useQuery") as jest.Mock).mockReturnValueOnce({
      error,
    });

    renderWithRouter(
      <MockedCache mocks={[]}>
        <App basepath="/" />
      </MockedCache>,
    );
    expect(screen.queryByTestId("apollo-error-alert")).toBeInTheDocument();
  });

  it("routes to PageHome page", () => {
    renderWithRouter(
      <MockedCache>
        <App basepath="/" />
      </MockedCache>,
    );
    expect(screen.getByTestId("PageHome")).toBeInTheDocument();
  });

  it("routes to PageNew page", () => {
    renderWithRouter(
      <MockedCache>
        <App basepath="/foo/bar" />
      </MockedCache>,
      {
        route: "/foo/bar/new",
      },
    );
    expect(screen.getByTestId("PageNew")).toBeInTheDocument();
  });

  describe(":slug routes", () => {
    it("redirects from ':slug/edit' to ':slug/edit/overview'", async () => {
      renderWithRouter(
        <MockedCache mocks={[mock]}>
          <App basepath="/" />
        </MockedCache>,
        {
          route: `/my-special-slug/edit`,
        },
      );

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
