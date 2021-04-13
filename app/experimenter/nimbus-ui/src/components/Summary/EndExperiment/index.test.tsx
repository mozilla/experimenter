/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import EndExperiment from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../../gql/experiments";
import { getStatus } from "../../../lib/experiment";
import {
  MockedCache,
  mockExperimentMutation,
  mockExperimentQuery,
} from "../../../lib/mocks";
import { getExperiment } from "../../../types/getExperiment";
import { NimbusExperimentStatus } from "../../../types/globalTypes";

describe("EndExperiment", () => {
  it("displays the end button when experiment is live", async () => {
    render(<Subject experiment={{}} />);
    await screen.findByTestId("end-experiment-start");
  });

  it("displays the ending UI when the experiment is ending", async () => {
    render(
      <Subject
        experiment={{
          isEndRequested: true,
        }}
      />,
    );
    await screen.findByTestId("experiment-ended-alert");
  });

  it("can start to but then cancel ending an experiment", async () => {
    render(<Subject />);

    const startEnd = await screen.findByTestId("end-experiment-start");
    fireEvent.click(startEnd);
    await screen.findByTestId("end-experiment-alert");

    const cancelEnd = await screen.findByTestId("end-experiment-cancel");
    fireEvent.click(cancelEnd);

    await screen.findByTestId("end-experiment-start");
  });

  it("can correctly end an experiment", async () => {
    render(<Subject withEndMock />);

    const startEnd = await screen.findByTestId("end-experiment-start");
    fireEvent.click(startEnd);
    await screen.findByTestId("end-experiment-alert");

    const confirmEnd = await screen.findByTestId("end-experiment-confirm");
    fireEvent.click(confirmEnd);
    await screen.findByTestId("experiment-ended-alert");
  });

  it("shows an error when something went wrong", async () => {
    render(<Subject withEndMock withMockedError />);

    const startEnd = await screen.findByTestId("end-experiment-start");
    fireEvent.click(startEnd);
    await screen.findByTestId("end-experiment-alert");

    const confirmEnd = await screen.findByTestId("end-experiment-confirm");
    fireEvent.click(confirmEnd);

    await screen.findByTestId("experiment-end-error");
  });
});

const Subject = ({
  experiment: overrides = {},
  withEndMock = false,
  withMockedError = false,
}: {
  experiment?: Partial<getExperiment["experimentBySlug"]>;
  withEndMock?: boolean;
  withMockedError?: boolean;
}) => {
  const { experiment } = mockExperimentQuery("demo-slug", {
    status: NimbusExperimentStatus.LIVE,
    ...overrides,
  });
  const status = getStatus(experiment);

  const mocks = [];
  if (withEndMock) {
    const mock = mockExperimentMutation(
      UPDATE_EXPERIMENT_MUTATION,
      {
        id: experiment.id!,
        isEndRequested: true,
      },
      "updateExperiment",
    );

    if (withMockedError) {
      mock.result.data["updateExperiment"].message = "No can do";
    }

    mocks.push(mock);
  }

  return (
    <MockedCache {...{ mocks }}>
      <EndExperiment {...{ experiment, status }} />
    </MockedCache>
  );
};
