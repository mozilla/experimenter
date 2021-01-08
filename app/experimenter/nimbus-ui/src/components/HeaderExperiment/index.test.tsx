/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { screen, render } from "@testing-library/react";
import HeaderExperiment from ".";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";
import { humanDate } from "../../lib/dateUtils";
import { NimbusExperimentStatus } from "../../types/globalTypes";

describe("HeaderExperiment", () => {
  it("renders as expected", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    render(
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        endDate={experiment.endDate}
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

  it("displays expected dates", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
    });
    render(
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        endDate={experiment.endDate}
        status={mockGetStatus(experiment.status)}
      />,
    );
    expect(
      screen.getByTestId("header-experiment-status-active"),
    ).toHaveTextContent("Live");
    expect(screen.getByTestId("header-dates")).toHaveTextContent(
      humanDate(experiment.startDate!),
    );
    expect(screen.getByTestId("header-dates")).toHaveTextContent(
      humanDate(experiment.endDate!),
    );
  });
});
