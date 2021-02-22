/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { cleanup, render, screen } from "@testing-library/react";
import React from "react";
import HeaderExperiment from ".";
import { humanDate } from "../../lib/dateUtils";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";

const assertStatusLink = async (
  status: NimbusExperimentStatus,
  label: string,
  route: string,
) => {
  const { experiment } = mockExperimentQuery("demo-slug", {
    status,
  });
  render(
    <HeaderExperiment
      name={experiment.name}
      slug={experiment.slug}
      startDate={experiment.startDate}
      computedEndDate={experiment.computedEndDate}
      status={mockGetStatus(experiment.status)}
      summaryView
    />,
  );
  const statusLink = await screen.findByTestId("status-link");
  expect(statusLink).toHaveTextContent(label);
  expect(statusLink).toHaveAttribute("href", `/${route}`);
  cleanup();
};

describe("HeaderExperiment", () => {
  it("renders as expected", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    render(
      <HeaderExperiment
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
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
        computedEndDate={experiment.computedEndDate}
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
      humanDate(experiment.computedEndDate!),
    );
  });

  describe("summary view", () => {
    it("displays the return to experiments link", async () => {
      const { experiment } = mockExperimentQuery("demo-slug");
      render(
        <HeaderExperiment
          name={experiment.name}
          slug={experiment.slug}
          startDate={experiment.startDate}
          computedEndDate={experiment.computedEndDate}
          status={mockGetStatus(experiment.status)}
          summaryView
        />,
      );
      await screen.findByTestId("experiment-return");
    });

    it("displays the correct status links", async () => {
      await assertStatusLink(
        NimbusExperimentStatus.DRAFT,
        "Edit Experiment",
        "edit",
      );

      await assertStatusLink(
        NimbusExperimentStatus.REVIEW,
        "Go to Review",
        "request-review",
      );

      await assertStatusLink(
        NimbusExperimentStatus.COMPLETE,
        "Go to Design",
        "design",
      );
    });
  });
});
