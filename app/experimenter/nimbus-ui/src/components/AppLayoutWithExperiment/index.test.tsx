/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { act, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import AppLayoutWithExperiment, { POLL_INTERVAL } from ".";
import { BASE_PATH } from "../../lib/constants";
import { mockExperimentQuery } from "../../lib/mocks";
import { renderWithRouter, RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";

jest.useFakeTimers();

describe("AppLayoutWithExperiment", () => {
  it("renders as expected", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("AppLayoutWithExperiment")).toBeInTheDocument();
      expect(screen.getByTestId("page-title")).toBeInTheDocument();
      expect(screen.getByTestId("page-title")).toHaveTextContent("Howdy!");
      expect(screen.getByTestId("child")).toBeInTheDocument();
      expect(screen.getByTestId("header-experiment")).toBeInTheDocument();
      expect(screen.getByTestId("nav-sidebar")).toBeInTheDocument();
    });
  });

  it("can render without a title", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} withTitle={false} />);
    await waitFor(() => {
      expect(screen.getByTestId("AppLayoutWithExperiment")).toBeInTheDocument();
      expect(screen.queryByTestId("page-title")).not.toBeInTheDocument();
    });
  });

  it("does not render the sidebar if prop is set to false", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} sidebar={false} />);
    await waitFor(() => {
      expect(screen.queryByTestId("nav-sidebar")).not.toBeInTheDocument();
    });
  });

  it("renders not found screen", async () => {
    const { mock: notFoundMock } = mockExperimentQuery("demo-slug", null);
    render(<Subject mocks={[notFoundMock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("not-found")).toBeInTheDocument();
    });
  });

  describe("polling", () => {
    const { mock } = mockExperimentQuery("demo-slug");
    const { mock: updatedMock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });

    it("polls useExperiment when the prop is passed in", async () => {
      render(<Subject mocks={[mock, updatedMock]} polling />);
      await waitFor(() => {
        expect(
          screen.getByTestId("header-experiment-status-active"),
        ).toHaveTextContent("Draft");
      });

      jest.advanceTimersByTime(POLL_INTERVAL);
      await waitFor(() => {
        expect(
          screen.getByTestId("header-experiment-status-active"),
        ).toHaveTextContent("Review");
      });
    });

    it("does not poll useExperiment when the prop is not passed in", async () => {
      render(<Subject mocks={[mock, updatedMock]} />);
      await waitFor(() => {
        expect(
          screen.getByTestId("header-experiment-status-active"),
        ).toHaveTextContent("Draft");
      });

      jest.advanceTimersByTime(POLL_INTERVAL);
      await waitFor(() => {
        expect(
          screen.getByTestId("header-experiment-status-active"),
        ).toHaveTextContent("Draft");
      });
    });

    it("stops polling useExperiment when the prop is passed in and the user navigates to a page without polling", async () => {
      const {
        history: { navigate },
      } = renderWithRouter(<Subject mocks={[mock, updatedMock]} polling />, {
        route: "/demo-slug",
      });

      await waitFor(() => {
        expect(
          screen.getByTestId("header-experiment-status-active"),
        ).toHaveTextContent("Draft");
      });

      window.history.pushState({}, "", `${BASE_PATH}/demo-slug/edit/overview`);
      await act(() => navigate("/demo-slug/edit/overview"));

      jest.advanceTimersByTime(POLL_INTERVAL);
      // updatedMock should not be hit
      await waitFor(() => {
        expect(
          screen.getByTestId("header-experiment-status-active"),
        ).toHaveTextContent("Draft");
      });
    });
  });

  // TODO: EXP-733 some sort of after test cleanup, can't add tests after without errors
  it("renders loading screen", () => {
    render(<Subject />);
    expect(screen.getByTestId("page-loading")).toBeInTheDocument();
  });
});

const Subject = ({
  mocks = [],
  polling = false,
  sidebar = true,
  withTitle = true,
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
  polling?: boolean;
  sidebar?: boolean;
  withTitle?: boolean;
}) => (
  <RouterSlugProvider {...{ mocks }}>
    <AppLayoutWithExperiment
      title={withTitle ? "Howdy!" : undefined}
      testId="AppLayoutWithExperiment"
      {...{ polling, sidebar }}
    >
      {({ experiment }) => <p data-testid="child">{experiment.slug}</p>}
    </AppLayoutWithExperiment>
  </RouterSlugProvider>
);
