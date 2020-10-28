/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, waitFor, render, fireEvent } from "@testing-library/react";
import PageEditOverview from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";
import { MockedResponse } from "@apollo/client/testing";

const { mock } = mockExperimentQuery("demo-slug");
const { mock: notFoundMock } = mockExperimentQuery("demo-slug", null);

let origConsoleLog: typeof global.console.log;
let mockSubmit: Record<string, string> = {};

describe("PageEditOverview", () => {
  const Subject = ({
    mocks = [],
  }: {
    mocks?: MockedResponse<Record<string, any>>[];
  }) => {
    return (
      <RouterSlugProvider {...{ mocks }}>
        <PageEditOverview />
      </RouterSlugProvider>
    );
  };

  beforeEach(() => {
    origConsoleLog = global.console.log;
    global.console.log = jest.fn();
    mockSubmit = {
      name: "Foo bar baz",
      hypothesis: "Some thing",
      application: "firefox-desktop",
    };
  });

  afterEach(() => {
    global.console.log = origConsoleLog;
  });

  it("renders as expected", async () => {
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("PageEditOverview")).toBeInTheDocument();
      expect(screen.getByTestId("header-experiment")).toBeInTheDocument();
    });
  });

  it("handles form submission", async () => {
    render(<Subject mocks={[mock]} />);
    await waitFor(() => fireEvent.click(screen.getByTestId("submit")));
    expect(global.console.log).toHaveBeenCalledWith("SUBMIT TBD");
  });

  it("handles form next button", async () => {
    render(<Subject mocks={[mock]} />);
    await waitFor(() => fireEvent.click(screen.getByTestId("next")));
    expect(global.console.log).toHaveBeenCalledWith("NEXT TBD");
  });

  it("renders not found screen", async () => {
    render(<Subject mocks={[notFoundMock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("not-found")).toBeInTheDocument();
    });
  });

  it("renders loading screen", () => {
    render(<Subject />);
    expect(screen.getByTestId("page-loading")).toBeInTheDocument();
  });
});

// Mocking form component because validation is exercised in its own tests.
jest.mock("../FormOverview", () => ({
  __esModule: true,
  default: (props: {
    isLoading: boolean;
    submitErrors?: Record<string, string[]>;
    onSubmit: Function;
    onNext: (ev: React.FormEvent) => void;
    applications: string[];
  }) => {
    const handleSubmit = (ev: React.FormEvent) => {
      ev.preventDefault();
      props.onSubmit(mockSubmit, jest.fn());
    };
    const handleNext = (ev: React.FormEvent) => {
      ev.preventDefault();
      props.onNext(ev);
    };
    return (
      <div data-testid="FormOverview">
        <div data-testid="submitErrors">
          {JSON.stringify(props.submitErrors)}
        </div>
        <button data-testid="submit" onClick={handleSubmit} />
        <button data-testid="next" onClick={handleNext} />
      </div>
    );
  },
}));
