/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, render } from "@testing-library/react";
import HeaderExperiment from ".";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";

const { experiment } = mockExperimentQuery("demo-slug");

describe("HeaderExperiment", () => {
  it("renders as expected", () => {
    render(
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        status={mockGetStatus(experiment.status)}
      />,
    );
    expect(screen.getByTestId("header-experiment-name")).toHaveTextContent(
      "Open-architected background installation",
    );
    expect(screen.getByTestId("header-experiment-slug")).toHaveTextContent(
      "demo-slug",
    );
    expect(
      screen.getByTestId("header-experiment-status-active"),
    ).toHaveTextContent("Draft");
  });
});
