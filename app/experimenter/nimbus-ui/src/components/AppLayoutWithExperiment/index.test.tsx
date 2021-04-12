/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { navigate } from "@reach/router";
import { act, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import AppLayoutWithExperiment, { POLL_INTERVAL, RedirectCheck } from ".";
import { BASE_PATH } from "../../lib/constants";
import { mockExperimentQuery } from "../../lib/mocks";
import { renderWithRouter, RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentPublishStatus } from "../../types/globalTypes";

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

  it("renders not found if an experiment isn't found", async () => {
    const { mock } = mockExperimentQuery("demo-slug", null);
    render(<Subject mocks={[mock]} />);
    await screen.findByRole("heading", { name: "Experiment Not Found" });
  });

  describe("polling", () => {
    const { mock: initialMock } = mockExperimentQuery("demo-slug");
    const { mock: updatedMock } = mockExperimentQuery("demo-slug", {
      publishStatus: NimbusExperimentPublishStatus.WAITING,
    });

    it("polls useExperiment when the prop is passed in", async () => {
      render(<Subject mocks={[initialMock, updatedMock]} polling />);
      await screen.findByText("Draft", { selector: ".text-primary" });
      jest.advanceTimersByTime(POLL_INTERVAL);
      await screen.findByText("Review", { selector: ".text-primary" });
    });

    it("does not poll useExperiment when the prop is not passed in", async () => {
      render(<Subject mocks={[initialMock, updatedMock]} />);
      await screen.findByText("Draft", { selector: ".text-primary" });
      jest.advanceTimersByTime(POLL_INTERVAL);
      // Review would be the next state, so ensure Draft is still "primary"
      await screen.findByText("Draft", { selector: ".text-primary" });
    });

    it("stops polling when the user navigates to a page without it", async () => {
      const {
        history: { navigate },
      } = renderWithRouter(
        <Subject mocks={[initialMock, updatedMock]} polling />,
        {
          route: "/demo-slug",
        },
      );

      await screen.findByText("Draft", { selector: ".text-primary" });
      window.history.pushState({}, "", `${BASE_PATH}/demo-slug/edit/overview`);
      await act(() => navigate("/demo-slug/edit/overview"));

      jest.advanceTimersByTime(POLL_INTERVAL);
      // Review would be the next state, so ensure Draft is still "primary"
      await screen.findByText("Draft", { selector: ".text-primary" });
    });
  });

  it("can redirect you somewhere else", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      publishStatus: NimbusExperimentPublishStatus.REVIEW,
    });

    render(
      <Subject
        mocks={[mock]}
        redirect={({ status }) => {
          if (status.review) {
            return "request-review";
          }
        }}
      />,
    );

    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith(
        `${BASE_PATH}/${experiment.slug}/request-review`,
        {
          replace: true,
        },
      );
    });
  });
});

jest.useFakeTimers();

jest.mock("@reach/router", () => ({
  ...(jest.requireActual("@reach/router") as any),
  navigate: jest.fn(),
}));

const Subject = ({
  mocks = [],
  polling,
  title,
  redirect,
}: {
  mocks?: MockedResponse[];
  polling?: boolean;
  title?: string;
  redirect?: (check: RedirectCheck) => void;
}) => (
  <RouterSlugProvider {...{ mocks }}>
    <AppLayoutWithExperiment
      testId="AppLayoutWithExperiment"
      {...{ title, polling, redirect }}
    >
      {({ experiment }) => <p>{experiment.slug}</p>}
    </AppLayoutWithExperiment>
  </RouterSlugProvider>
);
