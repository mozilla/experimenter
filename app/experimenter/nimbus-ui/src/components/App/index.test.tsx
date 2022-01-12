/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import * as apollo from "@apollo/client";
import { MockedResponse } from "@apollo/client/testing";
import { screen, waitFor } from "@testing-library/react";
import React, { ReactNode } from "react";
import { act } from "react-dom/test-utils";
import App from ".";
import { REFETCH_DELAY } from "../../hooks";
import { BASE_PATH } from "../../lib/constants";
import { MockedCache, mockExperimentQuery } from "../../lib/mocks";
import { renderWithRouter } from "../../lib/test-utils";

const { mock } = mockExperimentQuery("my-special-slug");

describe("App", () => {
  it("displays loading when config is loading", () => {
    (jest.spyOn(apollo, "useQuery") as jest.Mock).mockReturnValueOnce({
      loading: true,
    });
    renderSubject([]);
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

    renderSubject([]);

    expect(screen.queryByTestId("refetch-alert")).toBeInTheDocument();
    act(() => {
      jest.advanceTimersByTime(REFETCH_DELAY);
    });
    await screen.findByTestId("apollo-error-alert");
    spy.mockRestore();
  });

  it("routes to PageHome page", async () => {
    const { navigate } = renderSubject();
    await act(() => navigate());
    expect(screen.getByTestId("PageHome")).toBeInTheDocument();
  });

  it("routes to PageNew page", async () => {
    const { navigate } = renderSubject();
    await act(() => navigate("/new"));
    expect(screen.getByTestId("PageNew")).toBeInTheDocument();
  });

  describe(":slug routes", () => {
    it("redirects from ':slug/edit' to ':slug/edit/overview'", async () => {
      const { navigate } = renderSubject();
      await act(() => navigate("/my-special-slug/edit"));
      await waitFor(() => {
        expect(screen.getByTestId("PageEditOverview")).toBeInTheDocument();
      });
    });
  });
});

const renderSubject = (
  mocks: MockedResponse<Record<string, any>>[] = [mock],
) => {
  const {
    history: { navigate },
  } = renderWithRouter(
    <MockedCache mocks={mocks}>
      <App />
    </MockedCache>,
    {
      route: `/my-special-slug/`,
    },
  );
  return {
    // Modified `navigate` to include BASE_PATH from constants
    navigate: (path = "") => navigate(`${BASE_PATH}${path}`),
  };
};

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
