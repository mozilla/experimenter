/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { mockExperimentQuery } from "../../../lib/mocks";
import TableHighlights from "../TableHighlights";
import { Subject } from "./mocks";

describe("TableWithTabComparison", () => {
  // This test exists to test that the relative comparison shows by default and
  // to test the tab text. Comparison value tests are in table tests.
  it("toggles between absolute and relative branch comparisons", async () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    render(<Subject Table={TableHighlights} {...{ experiment }} />);

    const relativeTab = screen.getByText("Relative uplift comparison");
    const absoluteTab = screen.getByText("Absolute comparison");

    expect(relativeTab).toHaveAttribute("aria-selected", "true");
    expect(absoluteTab).toHaveAttribute("aria-selected", "false");

    fireEvent.click(absoluteTab);

    expect(relativeTab).toHaveAttribute("aria-selected", "false");
    expect(absoluteTab).toHaveAttribute("aria-selected", "true");
  });
});
