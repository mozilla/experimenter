/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import AppErrorBoundary, { AppErrorAlert } from ".";

describe("AppErrorAlert", () => {
  it("renders a general error dialog", async () => {
    const { queryByTestId } = render(
      <AppErrorAlert error={new Error("boop")} />,
    );
    expect(queryByTestId("error-loading-app")).toBeInTheDocument();
    await screen.findByText("boop");
  });
});

describe("AppErrorBoundary", () => {
  let origError: typeof global.console.error;

  beforeEach(() => {
    origError = global.console.error;
    global.console.error = jest.fn();
  });

  afterEach(() => {
    global.console.error = origError;
  });

  it("renders children that do not cause exceptions", () => {
    const GoodComponent = () => <p data-testid="good-component">Hi</p>;

    render(
      <AppErrorBoundary>
        <GoodComponent />
      </AppErrorBoundary>,
    );

    expect(screen.queryByTestId("error-loading-app")).not.toBeInTheDocument();
  });

  it("renders a general error dialog on exception in child component", async () => {
    const BadComponent = () => {
      throw new Error("bad");
    };

    render(
      <AppErrorBoundary>
        <BadComponent />
      </AppErrorBoundary>,
    );

    expect(screen.queryByTestId("error-loading-app")).toBeInTheDocument();
    await screen.findByText("bad");
  });
});
