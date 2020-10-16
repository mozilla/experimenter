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
  it("routes to PageHome page", () => {
    render(<Subject path="/" />);
    expect(screen.getByTestId("PageHome")).toBeInTheDocument();
  });

  it("routes to PageNew page", () => {
    render(<Subject basepath="/foo/bar" path="/foo/bar/new" />);
    expect(screen.getByTestId("PageNew")).toBeInTheDocument();
  });

  const Subject = ({ basepath = "/", path = "/" }) => {
    let source = createMemorySource(path);
    let history = createHistory(source);

    return (
      <LocationProvider history={history}>
        <App {...{ basepath }} />
      </LocationProvider>
    );
  };
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
