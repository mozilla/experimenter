/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { Subject } from "./mocks";

describe("EndExperiment", () => {
  it("displays the end button when experiment is live", async () => {
    render(<Subject experiment={{}} />);
    await screen.findByTestId("end-experiment-start");
  });

  it("can start to but then cancel ending an experiment", async () => {
    render(<Subject />);

    const startEnd = await screen.findByTestId("end-experiment-start");
    fireEvent.click(startEnd);
    await screen.findByTestId("end-experiment-alert");

    const cancelEnd = await screen.findByTestId("end-experiment-cancel");
    fireEvent.click(cancelEnd);

    await screen.findByTestId("end-experiment-start");
  });

  it("calls onSubmit when ending an experiment", async () => {
    const onSubmit = jest.fn();
    render(<Subject {...{ onSubmit }} />);

    const startEnd = await screen.findByTestId("end-experiment-start");
    fireEvent.click(startEnd);
    await screen.findByTestId("end-experiment-alert");

    const confirmEnd = await screen.findByTestId("end-experiment-confirm");
    fireEvent.click(confirmEnd);
    expect(onSubmit).toHaveBeenCalled();
  });

  it("disables the buttons when loading", async () => {
    render(<Subject isLoading={true} />);

    const startEnd = await screen.findByTestId("end-experiment-start");
    expect(startEnd).toBeDisabled();
  });
});
