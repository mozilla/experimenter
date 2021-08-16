/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import HeaderExperiment from ".";
import { humanDate } from "../../lib/dateUtils";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";

describe("HeaderExperiment", () => {
  it("renders as expected", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    render(
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={false}
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
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={false}
      />,
    );
    expect(
      screen.getByTestId("header-experiment-status-active"),
    ).toHaveTextContent("Live");
    expect(screen.getByTestId("header-dates")).toHaveTextContent(
      humanDate(experiment.startDate!),
    );
    expect(screen.getByTestId("header-dates")).toHaveTextContent(
      humanDate(experiment.computedEndDate!),
    );
    expect(screen.getByTestId("header-dates")).toHaveTextContent("(14 days)");
  });
  it("renders with archived", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {});
    render(
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={true}
      />,
    );
    expect(screen.queryByText("Archived")).toBeInTheDocument();
  });
});
