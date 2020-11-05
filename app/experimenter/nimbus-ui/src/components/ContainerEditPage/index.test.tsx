/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import ContainerEditPage, { POLL_INTERVAL } from ".";
import { renderWithRouter, RouterSlugProvider } from "../../lib/test-utils";
import { mockExperimentQuery } from "../../lib/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { BASE_PATH } from "../../lib/constants";
import { act } from "react-dom/test-utils";

jest.useFakeTimers();

describe("ContainerEditPage", () => {
  it("renders as expected", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("ContainerEditPage")).toBeInTheDocument();
      expect(screen.getByTestId("page-title")).toBeInTheDocument();
      expect(screen.getByTestId("page-title")).toHaveTextContent("Howdy!");
      expect(screen.getByTestId("child")).toBeInTheDocument();
    });
  });

  it("renders not found screen", async () => {
    const { mock: notFoundMock } = mockExperimentQuery("demo-slug", null);
    render(<Subject mocks={[notFoundMock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("not-found")).toBeInTheDocument();
    });
  });

  it("polls useExperiment when the option is passed in", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    const { mock: updatedMock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    render(<Subject mocks={[mock, updatedMock]} polling />);
    await waitFor(() => {
      expect(screen.getByTestId("header-experiment-status")).toHaveTextContent(
        NimbusExperimentStatus.DRAFT,
      );
    });

    jest.advanceTimersByTime(POLL_INTERVAL);
    await waitFor(() => {
      expect(screen.getByTestId("header-experiment-status")).toHaveTextContent(
        NimbusExperimentStatus.REVIEW,
      );
    });
  });

  it("does not poll useExperiment when the option is not passed in", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    const { mock: updatedMock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    render(<Subject mocks={[mock, updatedMock]} />);
    await waitFor(() => {
      expect(screen.getByTestId("header-experiment-status")).toHaveTextContent(
        NimbusExperimentStatus.DRAFT,
      );
    });

    jest.advanceTimersByTime(POLL_INTERVAL);
    await waitFor(() => {
      expect(screen.getByTestId("header-experiment-status")).toHaveTextContent(
        NimbusExperimentStatus.DRAFT,
      );
    });
  });

  it("stops polling useExperiment when the option is passed in and the user navigates to a page without polling", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    const { mock: updatedMock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.REVIEW,
    });
    const {
      history: { navigate },
    } = renderWithRouter(<Subject mocks={[mock, updatedMock]} polling />, {
      route: "/demo-slug",
    });

    await waitFor(() => {
      expect(screen.getByTestId("header-experiment-status")).toHaveTextContent(
        NimbusExperimentStatus.DRAFT,
      );
    });

    window.history.pushState({}, "", `${BASE_PATH}/demo-slug/edit/overview`);
    await act(() => navigate("/demo-slug/edit/overview"));

    jest.advanceTimersByTime(POLL_INTERVAL);
    // updatedMock should not be hit
    await waitFor(() => {
      expect(screen.getByTestId("header-experiment-status")).toHaveTextContent(
        NimbusExperimentStatus.DRAFT,
      );
    });
  });

  // TODO: some sort of after test cleanup, can't add tests after without errors
  it("renders loading screen", () => {
    render(<Subject />);
    expect(screen.getByTestId("page-loading")).toBeInTheDocument();
  });
});

const Subject = ({
  mocks = [],
  polling = false,
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
  polling?: boolean;
}) => (
  <RouterSlugProvider {...{ mocks }}>
    <ContainerEditPage
      title="Howdy!"
      testId="ContainerEditPage"
      {...{ polling }}
    >
      {({ experiment }) => <p data-testid="child">{experiment.slug}</p>}
    </ContainerEditPage>
  </RouterSlugProvider>
);
