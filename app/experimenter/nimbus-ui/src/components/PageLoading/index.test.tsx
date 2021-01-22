/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import PageLoading from ".";

describe("PageLoading", () => {
  it("renders as expected", () => {
    render(<PageLoading />);
    const spinner = screen.getByTestId("spinner");
    expect(screen.getByTestId("page-loading")).toContainElement(spinner);
    expect(spinner).toHaveClass("spinner-border");
  });
});
