/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { cleanup, render, screen } from "@testing-library/react";
import React from "react";
import { NimbusExperimentStatus } from "../../../types/globalTypes";
import { Subject } from "./mocks";

const innerBar = () => {
  return screen
    .getByTestId("timeline-progress-bar")
    .querySelector(".progress-bar")!;
};

describe("SummaryTimeline", () => {
  it("renders with a draft, in-review, and accepted experiment", () => {
    [
      NimbusExperimentStatus.DRAFT,
      NimbusExperimentStatus.REVIEW,
      NimbusExperimentStatus.ACCEPTED,
    ].forEach((status) => {
      render(<Subject {...{ status }} />);

      expect(screen.queryByTestId("label-not-launched")).toBeInTheDocument();
      expect(screen.queryByTestId("label-start-date")).not.toBeInTheDocument();
      expect(screen.queryByTestId("label-end-date")).not.toBeInTheDocument();
      expect(screen.queryByTestId("label-duration-days")).toBeInTheDocument();
      expect(screen.queryByTestId("label-enrollment-days")).toBeInTheDocument();

      cleanup();
    });
  });

  it("renders with a live experiment", () => {
    render(<Subject status={NimbusExperimentStatus.LIVE} />);

    expect(innerBar().classList).toContain("progress-bar-animated");
    expect(innerBar().classList).toContain("progress-bar-striped");

    expect(screen.queryByTestId("label-not-launched")).not.toBeInTheDocument();
    expect(screen.queryByTestId("label-start-date")).toBeInTheDocument();
    expect(screen.queryByTestId("label-end-date")).toBeInTheDocument();
    expect(screen.queryByTestId("label-duration-days")).toBeInTheDocument();
    expect(screen.queryByTestId("label-enrollment-days")).toBeInTheDocument();
  });

  it("renders with a completed experiment", () => {
    render(<Subject status={NimbusExperimentStatus.COMPLETE} />);

    expect(innerBar().classList).toContain("bg-success");

    expect(screen.queryByTestId("label-not-launched")).not.toBeInTheDocument();
    expect(screen.queryByTestId("label-start-date")).toBeInTheDocument();
    expect(screen.queryByTestId("label-end-date")).toBeInTheDocument();
    expect(screen.queryByTestId("label-duration-days")).toBeInTheDocument();
    expect(screen.queryByTestId("label-enrollment-days")).toBeInTheDocument();
  });

  it("renders 0 days properly", () => {
    render(<Subject proposedDuration={0} proposedEnrollment={0} />);

    expect(screen.queryByTestId("label-duration-days")).toHaveTextContent(
      "0 days",
    );
    expect(screen.queryByTestId("label-enrollment-days")).toHaveTextContent(
      "0 days",
    );
  });
});
