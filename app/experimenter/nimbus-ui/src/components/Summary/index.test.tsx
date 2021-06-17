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
import { createMutationMock, reviewRequestedBaseProps, Subject } from "./mocks";

describe("Summary", () => {
  it("renders expected components", () => {
    render(<Subject />);
    expect(screen.getByTestId("summary-timeline")).toBeInTheDocument();
    expect(screen.queryByTestId("experiment-end")).not.toBeInTheDocument();
    expect(screen.getByTestId("table-summary")).toBeInTheDocument();
    expect(screen.getByTestId("table-audience")).toBeInTheDocument();
    expect(screen.queryAllByTestId("table-branch")).toHaveLength(2);
    expect(screen.getByTestId("branches-section-title")).toHaveTextContent(
      "Branches",
    );
  });

  it("renders end experiment badge if end is requested", async () => {
    render(
      <Subject
        props={{
          status: NimbusExperimentStatus.LIVE,
          statusNext: NimbusExperimentStatus.COMPLETE,
        }}
      />,
    );
    await screen.findByTestId("pill-end-requested");
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

  describe("ending an experiment", () => {
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

    it("handles approval of end as expected", async () => {
      const { experiment } = mockExperimentQuery("demo-slug", {
        ...reviewRequestedBaseProps,
        canReview: true,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatus.APPROVED,
        { changelogMessage: CHANGELOG_MESSAGES.END_APPROVED },
      );
      render(<Subject props={experiment} mocks={[mutationMock]} />);
      const approveButton = await screen.findByTestId("approve-request");
      fireEvent.click(approveButton);
      const openRemoteSettingsButton = await screen.findByTestId(
        "open-remote-settings",
      );
      fireEvent.click(openRemoteSettingsButton);
      await waitFor(() => {
        expect(mockWindowOpen).toHaveBeenCalledWith(
          experiment.reviewUrl,
          "_blank",
        );
      });
    });

    it("handles rejection of end as expected", async () => {
      const expectedReason = "This smells bad.";
      const { experiment } = mockExperimentQuery("demo-slug", {
        ...reviewRequestedBaseProps,
        canReview: true,
      });
      const mutationMock = createMutationMock(
        experiment.id!,
        NimbusExperimentPublishStatus.IDLE,
        { statusNext: null, changelogMessage: expectedReason },
      );
      render(<Subject props={experiment} mocks={[mutationMock]} />);
      const rejectButton = await screen.findByTestId("reject-request");
      fireEvent.click(rejectButton);
      const rejectSubmitButton = await screen.findByTestId("reject-submit");
      const rejectReasonField = await screen.findByTestId("reject-reason");
      fireEvent.change(rejectReasonField, {
        target: { value: expectedReason },
      });
      fireEvent.blur(rejectReasonField);
      fireEvent.click(rejectSubmitButton);
      await waitFor(() =>
        expect(screen.queryByTestId("submit-error")).not.toBeInTheDocument(),
      );
    });
  });
});
