/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import {
  createMemorySource,
  createHistory,
  LocationProvider,
} from "@reach/router";
import App from ".";

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

  it("redirects from ':slug/edit' to ':slug/edit/overview'", () => {
    // WIP
    // jest.mock("@reach/router", () => ({
    //   redirect: jest.fn().mockImplementation(() => <span>Redirecting</span>),
    // }));
    // render(<Subject basepath="/experiments/nimbus" path="/my-slug/edit" />);
    // expect(MockRedirect).toHaveBeenCalledTimes(1);
    // expect(screen.getByTestId("PageEditOverview")).toBeInTheDocument();
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
