/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "../../lib/constants";
import { mockExperimentQuery } from "../../lib/mocks";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import { createMutationMock, Subject } from "./mocks";

describe("Summary", () => {
  it("renders expected components", () => {
    render(<Subject />);
    expect(screen.getByTestId("summary-timeline")).toBeInTheDocument();
    expect(screen.queryByTestId("experiment-end")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("link-monitoring-dashboard"),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("table-overview")).toBeInTheDocument();
    expect(screen.getByTestId("table-audience")).toBeInTheDocument();
    expect(screen.queryAllByTestId("table-branch")).toHaveLength(2);
    expect(screen.getByTestId("branches-section-title")).toHaveTextContent(
      "Branches",
    );
  });

  it("renders monitoring dashboard URL if experiment has been launched", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatus.LIVE,
        }}
      />,
    );

    await screen.findByTestId("link-monitoring-dashboard");
  });

  it("does not render monitoring dashboard URL if experiment has not been launched", () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatus.DRAFT,
        }}
      />,
    );

    expect(
      screen.queryByTestId("link-monitoring-dashboard"),
    ).not.toBeInTheDocument();
  });

  it("renders signoff table if experiment has been launched", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatus.LIVE,
        }}
      />,
    );

    await screen.findByTestId("table-signoff");
  });

  it("does not render signoff table if experiment has not been launched", () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatus.DRAFT,
        }}
      />,
    );

    expect(screen.queryByTestId("table-signoff")).not.toBeInTheDocument();
  });

  it("renders enrollment active badge if enrollment is not paused", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatus.LIVE,
          isEnrollmentPaused: false,
        }}
      />,
    );
    await screen.findByTestId("pill-enrolling-active");
  });

  it("renders enrollment complete badge if enrollment is not paused", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatus.LIVE,
          isEnrollmentPaused: true,
          enrollmentEndDate: new Date().toISOString(),
        }}
      />,
    );
    await screen.findByTestId("pill-enrolling-complete");
  });

  describe("ending an experiment request", () => {
    const origWindowOpen = global.window.open;
    let mockWindowOpen: any;

    beforeEach(() => {
      mockWindowOpen = jest.fn();
      global.window.open = mockWindowOpen;
    });

    afterEach(() => {
      global.window.open = origWindowOpen;
    });

    it("can mark the experiment as requesting review on end confirmation", async () => {
      const refetch = jest.fn();
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatus.LIVE,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatus.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END,
          status: NimbusExperimentStatus.LIVE,
          statusNext: NimbusExperimentStatus.COMPLETE,
        },
      );
      render(
        <Subject props={experiment} mocks={[mutationMock]} {...{ refetch }} />,
      );
      fireEvent.click(screen.getByTestId("end-experiment-start"));
      await screen.findByTestId("end-experiment-alert");
      fireEvent.click(screen.getByTestId("end-experiment-confirm"));
      await waitFor(() => {
        expect(refetch).toHaveBeenCalled();
        expect(screen.queryByTestId("submit-error")).not.toBeInTheDocument();
      });
    });

    it("handles submission with server API error", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatus.LIVE,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatus.REVIEW,
        { changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END },
      );
      mutationMock.result.errors = [new Error("Boo")];
      render(<Subject props={experiment} mocks={[mutationMock]} />);
      fireEvent.click(screen.getByTestId("end-experiment-start"));
      await screen.findByTestId("end-experiment-alert");
      fireEvent.click(screen.getByTestId("end-experiment-confirm"));
      const errorContainer = await screen.findByTestId("submit-error");
      expect(errorContainer).toHaveTextContent(SUBMIT_ERROR);
    });

    it("handles submission with server-side validation errors", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatus.LIVE,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatus.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END,
          statusNext: NimbusExperimentStatus.COMPLETE,
          status: NimbusExperimentStatus.LIVE,
        },
      );
      const errorMessage = "Something went very wrong.";
      mutationMock.result.data.updateExperiment.message = {
        status: [errorMessage],
      };
      render(<Subject props={experiment} mocks={[mutationMock]} />);
      fireEvent.click(screen.getByTestId("end-experiment-start"));
      await screen.findByTestId("end-experiment-alert");
      fireEvent.click(screen.getByTestId("end-experiment-confirm"));
      const errorContainer = await screen.findByTestId("submit-error");
      expect(errorContainer).toHaveTextContent(errorMessage);
    });
  });

  describe("ending enrollment for an experiment request", () => {
    const origWindowOpen = global.window.open;
    let mockWindowOpen: any;

    beforeEach(() => {
      mockWindowOpen = jest.fn();
      global.window.open = mockWindowOpen;
    });

    afterEach(() => {
      global.window.open = origWindowOpen;
    });

    it("can mark the experiment as requesting review on enrollment end confirmation", async () => {
      const refetch = jest.fn();
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatus.LIVE,
        statusNext: null,
        isEnrollmentPaused: false,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatus.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END_ENROLLMENT,
          status: NimbusExperimentStatus.LIVE,
          statusNext: NimbusExperimentStatus.LIVE,
          isEnrollmentPaused: true,
        },
      );
      render(
        <Subject props={experiment} mocks={[mutationMock]} {...{ refetch }} />,
      );
      fireEvent.click(screen.getByTestId("end-enrollment-start"));
      await screen.findByTestId("end-enrollment-alert");
      fireEvent.click(screen.getByTestId("end-enrollment-confirm"));
      await waitFor(() => {
        expect(refetch).toHaveBeenCalled();
        expect(screen.queryByTestId("submit-error")).not.toBeInTheDocument();
      });
    });

    it("handles submission with server API error", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatus.LIVE,
        isEnrollmentPaused: false,
        statusNext: null,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatus.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END_ENROLLMENT,
        },
      );
      mutationMock.result.errors = [new Error("Boo")];
      render(<Subject props={experiment} mocks={[mutationMock]} />);
      fireEvent.click(screen.getByTestId("end-enrollment-start"));
      await screen.findByTestId("end-enrollment-alert");
      fireEvent.click(screen.getByTestId("end-enrollment-confirm"));
      const errorContainer = await screen.findByTestId("submit-error");
      expect(errorContainer).toHaveTextContent(SUBMIT_ERROR);
    });

    it("handles submission with server-side validation errors", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatus.LIVE,
        isEnrollmentPaused: false,
        statusNext: null,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatus.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END_ENROLLMENT,
          statusNext: NimbusExperimentStatus.LIVE,
          status: NimbusExperimentStatus.LIVE,
          isEnrollmentPaused: true,
        },
      );
      const errorMessage = "Something went very wrong.";
      mutationMock.result.data.updateExperiment.message = {
        status: [errorMessage],
      };
      render(<Subject props={experiment} mocks={[mutationMock]} />);
      fireEvent.click(screen.getByTestId("end-enrollment-start"));
      await screen.findByTestId("end-enrollment-alert");
      fireEvent.click(screen.getByTestId("end-enrollment-confirm"));
      const errorContainer = await screen.findByTestId("submit-error");
      expect(errorContainer).toHaveTextContent(errorMessage);
    });
  });
});
