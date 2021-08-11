/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import * as apollo from "@apollo/client";
import { screen, waitFor } from "@testing-library/react";
import React, { ReactNode } from "react";
import { act } from "react-dom/test-utils";
import App from ".";
import { REFETCH_DELAY } from "../../hooks";
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

  it("renders the error alerts when an error occurs querying the config", async () => {
    jest.useFakeTimers();
    const error = new Error("boop");
    const refetch = jest.fn();

    const spy = (jest.spyOn(apollo, "useQuery") as jest.Mock).mockReturnValue({
      error,
      refetch,
    });

    renderWithRouter(
      <MockedCache mocks={[]}>
        <App basepath="/" />
      </MockedCache>,
    );
    expect(screen.queryByTestId("refetch-alert")).toBeInTheDocument();
    act(() => {
      jest.advanceTimersByTime(REFETCH_DELAY);
    });
    await screen.findByTestId("apollo-error-alert");
    spy.mockRestore();
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
