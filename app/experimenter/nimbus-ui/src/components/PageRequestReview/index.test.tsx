/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen } from "@testing-library/react";
import PageRequestReview from ".";
import { renderWithRouter } from "../../lib/helpers";

describe("PageRequestReview", () => {
  it("renders as expected", () => {
    renderWithRouter(<PageRequestReview />);
    expect(screen.getByTestId("PageRequestReview")).toBeInTheDocument();
  });
});
