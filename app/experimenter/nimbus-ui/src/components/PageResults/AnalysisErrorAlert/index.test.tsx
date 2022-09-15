/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import AnalysisErrorAlert from ".";
import { mockAnalysisWithErrors } from "../../../lib/visualization/mocks";
import AnalysisErrorMessage from "./AnalysisErrorMessage";

describe("AnalysisErrorAlert", () => {
  it("renders errors as expected", () => {
    const errors = mockAnalysisWithErrors().errors.experiment;
    render(<AnalysisErrorAlert errors={errors} />);

    expect(screen.getByText("Analysis errors during last run:"));
    expect(screen.getByText("NoEnrollmentPeriodException"));

    expect(screen.getByTestId("error-help-url")).toHaveProperty(
      "href",
      "https://mozilla.slack.com/archives/CF94YGE03",
    );
  });
});

describe("AnalysisErrorMessage", () => {
  it("renders a metric error as expected", () => {
    const err = mockAnalysisWithErrors().errors.picture_in_picture[0];
    render(<AnalysisErrorMessage err={err} />);

    expect(
      screen.getByText(
        "StatisticComputationException calculating bootstrap_mean",
      ),
    );

    expect(screen.getByText(err.message, { exact: false }));
  });

  it("displays unknown error message", () => {
    const err = mockAnalysisWithErrors().errors.picture_in_picture[0];
    err.exception_type = "";
    render(<AnalysisErrorMessage err={err} />);

    expect(screen.getByText("Unknown error calculating bootstrap_mean"));

    expect(screen.getByText(err.message, { exact: false }));
  });
});
