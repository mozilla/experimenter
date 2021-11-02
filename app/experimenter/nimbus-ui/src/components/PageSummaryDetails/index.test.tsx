/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import { mockExperimentQuery } from "../../lib/mocks";
import { Subject } from "./mocks";

jest.mock("@reach/router", () => ({
  ...(jest.requireActual("@reach/router") as any),
  navigate: jest.fn(),
}));

describe("PageSummaryDetail", () => {
  it("renders as expected", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await screen.findByTestId("PageSummaryDetails");
    expect(screen.getByTestId("summary")).toBeInTheDocument();
    screen.getByRole("navigation");
  });
});
