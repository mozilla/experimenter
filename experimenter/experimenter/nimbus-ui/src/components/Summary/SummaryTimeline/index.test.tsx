/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { cleanup, render, screen } from "@testing-library/react";
import React from "react";
import { Subject } from "src/components/Summary/SummaryTimeline/mocks";
import { TOOLTIP_DURATION } from "src/lib/constants";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "src/types/globalTypes";

const innerBar = () => {
  return screen
    .getByTestId("timeline-progress-bar")
    .querySelector(".progress-bar")!;
};

describe("SummaryTimeline", () => {
  it("renders with a draft, in-review, and accepted/waiting experiment", () => {
    [
      { status: NimbusExperimentStatusEnum.DRAFT },
      { publishStatus: NimbusExperimentPublishStatusEnum.REVIEW },
      { publishStatus: NimbusExperimentPublishStatusEnum.WAITING },
    ].forEach((set) => {
      render(<Subject {...set} />);

      expect(screen.queryByTestId("label-not-launched")).toBeInTheDocument();
      expect(screen.queryByTestId("label-start-date")).not.toBeInTheDocument();
      expect(screen.queryByTestId("label-release-date")).toBeNull();
      expect(
        screen.queryByTestId("label-enrollment-end-date"),
      ).not.toBeInTheDocument();
      expect(screen.queryByTestId("label-end-date")).not.toBeInTheDocument();
      expect(screen.queryByTestId("label-duration-days")).toBeInTheDocument();
      expect(screen.queryByTestId("label-enrollment-days")).toBeInTheDocument();

      cleanup();
    });
  });

  it("renders with a live experiment", async () => {
    render(<Subject status={NimbusExperimentStatusEnum.LIVE} />);

    expect(innerBar().classList).toContain("progress-bar-animated");
    expect(innerBar().classList).toContain("progress-bar-striped");

    expect(screen.queryByTestId("label-not-launched")).not.toBeInTheDocument();
    expect(screen.queryByTestId("label-start-date")).toBeInTheDocument();
    expect(
      screen.queryByTestId("label-enrollment-end-date"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("label-end-date")).toBeInTheDocument();
    expect(screen.queryByTestId("label-duration-days")).toBeInTheDocument();
    expect(screen.queryByTestId("label-enrollment-days")).toBeInTheDocument();
    expect(
      await screen.findByTestId("tooltip-duration-summary"),
    ).toHaveAttribute("data-tip", TOOLTIP_DURATION);
  });

  it("renders with a live rollout", async () => {
    render(
      <Subject status={NimbusExperimentStatusEnum.LIVE} isRollout={true} />,
    );

    expect(innerBar().classList).toContain("progress-bar-animated");
    expect(innerBar().classList).toContain("progress-bar-striped");

    expect(screen.getByTestId("label-start-date")).toBeInTheDocument();
    expect(screen.getByTestId("label-end-date")).toBeInTheDocument();
    expect(screen.getByTestId("label-duration-days")).toBeInTheDocument();

    expect(screen.queryByTestId("label-not-launched")).toBeNull();
    expect(screen.queryByTestId("label-enrollment-end-date")).toBeNull();
    expect(screen.queryByTestId("label-enrollment-days")).toBeNull();
    expect(
      await screen.findByTestId("tooltip-duration-summary"),
    ).toHaveAttribute("data-tip", TOOLTIP_DURATION);
  });

  it("renders with a completed experiment", () => {
    render(<Subject status={NimbusExperimentStatusEnum.COMPLETE} />);

    expect(innerBar().classList).toContain("bg-success");

    expect(screen.queryByTestId("label-not-launched")).not.toBeInTheDocument();
    expect(screen.queryByTestId("label-start-date")).toBeInTheDocument();
    expect(
      screen.queryByTestId("label-enrollment-end-date"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("label-end-date")).toBeInTheDocument();
    expect(screen.queryByTestId("label-duration-days")).toBeInTheDocument();
    expect(screen.queryByTestId("label-enrollment-days")).toBeInTheDocument();
  });

  it("renders 0 days properly", () => {
    render(<Subject computedDurationDays={0} computedEnrollmentDays={0} />);

    expect(screen.queryByTestId("label-duration-days")).toHaveTextContent(
      "0 days",
    );
    expect(screen.queryByTestId("label-enrollment-days")).toHaveTextContent(
      "0 days",
    );
  });
});
