/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import HeaderExperiment from "src/components/HeaderExperiment";
import { BASE_PATH } from "src/lib/constants";
import { humanDate } from "src/lib/dateUtils";
import { mockExperimentQuery, mockGetStatus } from "src/lib/mocks";
import { NimbusExperimentStatusEnum } from "src/types/globalTypes";

describe("HeaderExperiment", () => {
  it("renders as expected", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    render(
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={false}
        isRollout={false}
      />,
    );
    expect(
      screen.queryByTestId("header-experiment-parent"),
    ).not.toBeInTheDocument();
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

  it("displays parent experiment link when cloned", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    const { experiment: parent } = mockExperimentQuery("parent-demo-slug", {
      name: "Parent Demo Slug",
    });
    render(
      <HeaderExperiment
        parent={parent}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={false}
        isRollout={false}
      />,
    );

    const parentLine = screen.queryByTestId("header-experiment-parent");
    expect(parentLine).toBeInTheDocument();

    const parentLink = parentLine?.querySelector("a");
    expect(parentLink).toBeInTheDocument();

    expect(parentLink!).toHaveTextContent(parent.name);
    expect(parentLink!).toHaveAttribute("href", `${BASE_PATH}/${parent.slug}`);
  });

  it("displays expected dates", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.LIVE,
    });
    render(
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={false}
        isRollout={false}
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
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={true}
        isRollout={false}
      />,
    );
    expect(screen.queryByText("Archived")).toBeInTheDocument();
  });

  it("renders with rollout", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {});
    render(
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={false}
        isRollout={true}
      />,
    );
    expect(screen.queryByText("Rollout")).toBeInTheDocument();
  });

  it("copies experiment slug to clipboard when copy button is clicked", async () => {
    const { experiment } = mockExperimentQuery("my-test-experiment", {});
    render(
      <HeaderExperiment
        parent={null}
        name={experiment.name}
        slug={experiment.slug}
        startDate={experiment.startDate}
        computedEndDate={experiment.computedEndDate}
        computedDurationDays={experiment.computedDurationDays}
        status={mockGetStatus(experiment)}
        isArchived={false}
        isRollout={true}
      />,
    );
    const copyButton = screen.getByRole("button");

    // const clipboard = {
    //   writeText: jest.fn().mockResolvedValue(undefined),
    // };
    // const navigator = {
    //   clipboard,
    // };
    // // @ts-ignore
    // global.navigator = navigator;

    Object.assign(navigator, {
      clipboard: {
        writeText: () => {},
      },
    });

    jest.spyOn(navigator.clipboard, "writeText");

    await userEvent.click(copyButton);
    // fireEvent.click(copyButton);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      "my-test-experiment",
    );
    expect(navigator.clipboard.writeText).toBeCalledTimes(1);
  });
});
