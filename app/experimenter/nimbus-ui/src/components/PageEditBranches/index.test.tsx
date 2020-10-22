/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen } from "@testing-library/react";
import PageEditBranches from ".";
import { renderWithRouter } from "../../lib/helpers";

describe("PageEditBranches", () => {
  it("renders as expected", () => {
    renderWithRouter(<PageEditBranches />);
    expect(screen.getByTestId("PageEditBranches")).toBeInTheDocument();
  });
});
