/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import PageNew from ".";

describe("PageNew", () => {
  let origConsoleLog: typeof global.console.log;

  beforeEach(() => {
    origConsoleLog = global.console.log;
    global.console.log = jest.fn();
  });

  afterEach(() => {
    global.console.log = origConsoleLog;
    cleanup();
  });

  it("renders as expected", async () => {
    render(<Subject />);
    expect(screen.getByTestId("PageNew")).toBeInTheDocument();
  });

  it("handles experiment form submission", () => {
    render(<Subject />);
    fireEvent.click(screen.getByTestId("submit"));
    expect(global.console.log).toHaveBeenCalledWith("CREATE TBD", {
      name: "Foo bar baz",
      hypothesis: "Some thing",
      application: "firefox-desktop",
    });
  });

  it("handles experiment form cancellation", () => {
    render(<Subject />);
    fireEvent.click(screen.getByTestId("cancel"));
    expect(global.console.log).toHaveBeenCalledWith("CANCEL TBD");
  });

  const Subject = () => {
    return <PageNew />;
  };
});

// Mocking form component because validation is exercised in its own tests.
jest.mock("../FormExperimentOverviewPartial", () => ({
  __esModule: true,
  default: (props: {
    onSubmit: Function;
    onCancel: (ev: React.FormEvent) => void;
    applications: string[];
  }) => {
    const handleSubmit = (ev: React.FormEvent) => {
      ev.preventDefault();
      props.onSubmit({
        name: "Foo bar baz",
        hypothesis: "Some thing",
        application: "firefox-desktop",
      });
    };
    const handleCancel = (ev: React.FormEvent) => {
      ev.preventDefault();
      props.onCancel(ev);
    };
    return (
      <div data-testid="FormExperimentOverviewPartial">
        <button data-testid="submit" onClick={handleSubmit} />
        <button data-testid="cancel" onClick={handleCancel} />
      </div>
    );
  },
}));
