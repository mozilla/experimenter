/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { act, render, screen } from "@testing-library/react";
import React from "react";
import { REFETCH_DELAY } from ".";
import Subject from "./mocks";

describe("useRefetchOnError", () => {
  it("returns RefetchAlert, then returns ApolloErrorAlert when an error occurs after refetch", async () => {
    render(<Subject noValidQueries />);
    await screen.findByTestId("refetch-alert");
    act(() => {
      jest.advanceTimersByTime(REFETCH_DELAY);
    });
    await screen.findByTestId("apollo-error-alert");
  });

  it("returns RefetchAlert, then renders expected content on success", async () => {
    render(<Subject />);
    await screen.findByTestId("refetch-alert");
    act(() => {
      jest.advanceTimersByTime(REFETCH_DELAY);
    });
    await screen.findByText("No errors!");
  });
});

jest.useFakeTimers();
