/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "../../lib/constants";
import { mockExperimentQuery } from "../../lib/mocks";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
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

  it("hides expected content when withFullDetails = false", () => {
    render(<Subject withFullDetails={false} />);
    expect(screen.getByTestId("summary-timeline")).toBeInTheDocument();
    expect(screen.queryByTestId("experiment-end")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("link-monitoring-dashboard"),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("table-overview")).toBeInTheDocument();
    expect(screen.getByTestId("table-audience")).toBeInTheDocument();
    expect(screen.queryAllByTestId("table-branch")).toHaveLength(0);
  });

  it("renders signoff table if experiment has been launched", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.LIVE,
        }}
      />,
    );

    await screen.findByTestId("table-signoff");
  });

  it("does not render signoff table if experiment has not been launched", () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.DRAFT,
        }}
      />,
    );

    expect(screen.queryByTestId("table-signoff")).not.toBeInTheDocument();
  });

  it("renders enrollment active badge if enrollment is not paused", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.LIVE,
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
          status: NimbusExperimentStatusEnum.LIVE,
          isEnrollmentPaused: true,
          enrollmentEndDate: new Date().toISOString(),
        }}
      />,
    );
    await screen.findByTestId("pill-enrolling-complete");
  });

  it("renders the end experiment button if the experiment is live and idle", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.LIVE,
          publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
        }}
      />,
    );
    await screen.findByText("End Experiment");
  });

  it("renders the cancel review button if the experiment is in review state", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.LIVE,
          publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
        }}
      />,
    );
    await screen.findByText("Cancel Review Request");
  });

  it("does not renders the end experiment button if the experiment is live and not idle", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatusEnum.LIVE,
          publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
        }}
      />,
    );
    expect(screen.queryByText("End Experiment")).not.toBeInTheDocument();
    expect(
      screen.queryByText("End Enrollment for Experiment"),
    ).not.toBeInTheDocument();
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
        status: NimbusExperimentStatusEnum.LIVE,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END,
          status: NimbusExperimentStatusEnum.LIVE,
          statusNext: NimbusExperimentStatusEnum.COMPLETE,
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

    it("can cancel review when the experiment is in review state", async () => {
      const refetch = jest.fn();
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatusEnum.LIVE,
        publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.IDLE,
        {
          changelogMessage: CHANGELOG_MESSAGES.CANCEL_REVIEW,
        },
      );
      render(
        <Subject props={experiment} mocks={[mutationMock]} {...{ refetch }} />,
      );

      await screen.findByTestId("cancel-review-start");
      fireEvent.click(screen.getByTestId("cancel-review-start"));
      await screen.findByTestId("cancel-review-alert");
      fireEvent.click(screen.getByTestId("cancel-review-confirm"));
      await waitFor(() => {
        expect(refetch).toHaveBeenCalled();
        expect(screen.queryByTestId("submit-error")).not.toBeInTheDocument();
      });
    });

    it("handles submission with server API error", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatusEnum.LIVE,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
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
        status: NimbusExperimentStatusEnum.LIVE,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END,
          statusNext: NimbusExperimentStatusEnum.COMPLETE,
          status: NimbusExperimentStatusEnum.LIVE,
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
        status: NimbusExperimentStatusEnum.LIVE,
        statusNext: null,
        isEnrollmentPaused: false,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END_ENROLLMENT,
          status: NimbusExperimentStatusEnum.LIVE,
          statusNext: NimbusExperimentStatusEnum.LIVE,
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
        status: NimbusExperimentStatusEnum.LIVE,
        isEnrollmentPaused: false,
        statusNext: null,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
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
        status: NimbusExperimentStatusEnum.LIVE,
        isEnrollmentPaused: false,
        statusNext: null,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatusEnum.REVIEW,
        {
          changelogMessage: CHANGELOG_MESSAGES.REQUESTED_REVIEW_END_ENROLLMENT,
          statusNext: NimbusExperimentStatusEnum.LIVE,
          status: NimbusExperimentStatusEnum.LIVE,
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
