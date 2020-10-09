/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { ReactNode } from "react";
import "./services/config";
import "./services/sentry";

// Mock out these components - for testing, we only care that they're used
jest.mock("react", () => ({
  ...jest.requireActual("react"),
  StrictMode: ({ children }: { children: ReactNode }) => (
    <div data-testid="StrictMode">{children}</div>
  ),
}));

jest.mock("./components/AppErrorBoundary", () => ({
  __esModule: true,
  default: ({ children }: { children: ReactNode }) => (
    <div data-testid="AppErrorBoundary">{children}</div>
  ),
}));

jest.mock("@apollo/client", () => ({
  ...jest.requireActual("@apollo/client"),
  ApolloProvider: ({ children }: { children: ReactNode }) => (
    <div data-testid="ApolloProvider">{children}</div>
  ),
}));

jest.mock("./components/App", () => ({
  __esModule: true,
  default: ({ children }: { children: ReactNode }) => (
    <div data-testid="App">{children}</div>
  ),
}));

describe("index", () => {
  const origError = global.console.error;
  let mockError: any, mockConfig: any, mockSentry: any;

  beforeEach(() => {
    jest.resetModules();

    const div = document.createElement("div");
    div.id = "root";
    document.body.appendChild(div);

    mockConfig = { readConfig: jest.fn() };
    mockSentry = { configure: jest.fn() };

    jest.mock("./services/config", () => mockConfig);
    jest.mock("./services/sentry", () => mockSentry);

    mockError = jest.fn();
    global.console.error = mockError;
  });

  afterEach(() => {
    global.console.error = origError;
  });

  it("should render as expected", () => {
    require("./index");

    const root = document.getElementById("root")!;
    expect(mockConfig.readConfig).toHaveBeenCalledWith(root);

    // Assert that these mock components are nested.
    let currRoot: any = root;
    ["StrictMode", "AppErrorBoundary", "ApolloProvider", "App"].forEach(
      (name) => {
        currRoot = currRoot?.querySelector(`*[data-testid="${name}"]`);
        expect(currRoot).toBeDefined();
      },
    );
  });

  it("should configure sentry if DSN is available", () => {
    mockConfig.readConfig = jest.fn(() => {
      Object.assign(mockConfig, {
        sentry_dsn: "http://example.com/sentry",
        version: "1.0",
      });
    });
    require("./index");
    const root = document.getElementById("root")!;
    expect(mockConfig.readConfig).toHaveBeenCalledWith(root);
    expect(mockSentry.configure).toHaveBeenCalledWith(
      mockConfig.sentry_dsn,
      mockConfig.version,
    );
  });

  it("should log initialization errors", () => {
    mockConfig.readConfig = jest.fn(() => {
      throw new Error("uh oh");
    });
    require("./index");
    const root = document.getElementById("root")!;
    expect(mockConfig.readConfig).toHaveBeenCalledWith(root);
    expect(mockError).toHaveBeenCalled();
  });
});
