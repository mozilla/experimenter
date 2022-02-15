/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import * as apollo from "@apollo/client";
import { MockedResponse } from "@apollo/client/testing";
import { render, screen } from "@testing-library/react";
import React, { useContext } from "react";
import AppLayoutWithExperiment from ".";
import { ExperimentContext, RedirectCheck } from "../../lib/contexts";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import ExperimentRoot from "../App/ExperimentRoot";

describe("AppLayoutWithExperiment", () => {
  it("renders as expected with default props", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await screen.findByTestId("AppLayoutWithExperiment");
    await screen.findByTestId("nav-sidebar");
  });

  it("can render a page title", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    const title = "Howdy partner";
    render(<Subject mocks={[mock]} {...{ title }} />);
    await screen.findByRole("heading", { name: title });
  });

  it("renders loading screen to start", async () => {
    render(<Subject />);
    await screen.findByText("Loading...");
  });

  it("renders the error alert when an error occurs querying the experiment", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    const error = new Error("boop");
    const stopPolling = jest.fn();

    (jest.spyOn(apollo, "useQuery") as jest.Mock).mockReturnValueOnce({
      error,
      stopPolling,
    });

    render(<Subject mocks={[mock]} />);
    expect(screen.queryByTestId("apollo-error-alert")).toBeInTheDocument();
  });

  it("renders not found if an experiment isn't found", async () => {
    const { mock } = mockExperimentQuery("demo-slug", null);
    render(<Subject mocks={[mock]} />);
    await screen.findByRole("heading", { name: "Experiment Not Found" });
  });

  // Commented out until fixed in #7085
  // it("renders the error warning when an error occurs polling the experiment", async () => {
  //   jest.useFakeTimers();
  //   const { mock: initialMock } = mockExperimentQuery("demo-slug");
  //   const { mock: updatedMock } = mockExperimentQuery("demo-slug", {
  //     publishStatus: NimbusExperimentPublishStatusEnum.WAITING,
  //   });
  //   const mockWithError = { ...initialMock, error: new Error("boop") };
  //   render(
  //     <Subject mocks={[initialMock, mockWithError, updatedMock]} polling />,
  //   );
  //   await screen.findByText("Draft", { selector: ".text-primary" });
  //   expect(screen.queryByTestId("polling-error-alert")).not.toBeInTheDocument();

  //   jest.advanceTimersByTime(POLL_INTERVAL);
  //   await screen.findByTestId("polling-error-alert");
  //   expect(
  //     screen.queryByText("30 seconds", { exact: false }),
  //   ).toBeInTheDocument();

  //   // error is hidden when polling works as expected, should show updatedMock
  //   jest.advanceTimersByTime(POLL_INTERVAL);
  //   await screen.findByText("Review", { selector: ".text-primary" });
  //   expect(screen.queryByTestId("polling-error-alert")).not.toBeInTheDocument();
  // });
});

const Subject = ({
  mocks = [],
  title,
  redirect,
  polling = false,
  disableSingleExperimentHack = true,
}: {
  mocks?: MockedResponse[];
  polling?: boolean;
  title?: string;
  redirect?: (check: RedirectCheck) => void;
  disableSingleExperimentHack?: boolean;
}) => (
  <RouterSlugProvider {...{ mocks, disableSingleExperimentHack }}>
    <ExperimentRoot basepath="/">
      <AppLayoutWithExperiment {...{ title, redirect }}>
        {polling ? <SubjectInnerWithPolling /> : <SubjectInner />}
      </AppLayoutWithExperiment>
    </ExperimentRoot>
  </RouterSlugProvider>
);

const SubjectInner = () => {
  const { experiment } = useContext(ExperimentContext)!;
  return <p>{experiment.slug}</p>;
};

const SubjectInnerWithPolling = () => {
  const { experiment, useExperimentPolling } = useContext(ExperimentContext)!;
  useExperimentPolling();
  return <p>{experiment.slug}</p>;
};
