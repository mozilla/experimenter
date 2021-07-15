/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import fetchMock from "jest-fetch-mock";
import React from "react";
import { CHANGELOG_MESSAGES, SERVER_ERRORS } from "../../lib/constants";
import { mockExperimentQuery } from "../../lib/mocks";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import { createMutationMock } from "../Summary/mocks";
import {
  createFullStatusMutationMock,
  createStatusMutationMock,
  endReviewRequestedBaseProps,
  enrollmentPauseReviewRequestedBaseProps,
  reviewRequestedBaseProps,
  Subject,
} from "./mocks";

jest.mock("@reach/router", () => ({
  ...(jest.requireActual("@reach/router") as any),
  navigate: jest.fn(),
}));

describe("PageSummary", () => {
  const origError = global.console.error;
  const origWindowOpen = global.window.open;

  let mockError: any;

  beforeAll(() => {
    fetchMock.enableMocks();
  });

  beforeEach(() => {
    mockError = jest.fn();
    global.console.error = mockError;
  });

  afterEach(() => {
    global.console.error = origError;
    global.window.open = origWindowOpen;
  });

  afterAll(() => {
    fetchMock.disableMocks();
  });

  async function checkRequiredBoxes() {
    const checkboxes = screen.queryAllByTestId("required-checkbox");

    for (const checkbox of checkboxes) {
      await act(async () => void fireEvent.click(checkbox));
    }
  }

  it("renders as expected", async () => {
    const { mock } = mockExperimentQuery("demo-slug");
    render(<Subject mocks={[mock]} />);
    await screen.findByTestId("PageSummary");
    await screen.findByTestId("start-launch-draft-to-review");
    expect(screen.getByTestId("summary")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId("summary-page-signoff")).toBeInTheDocument();
    });
    screen.getByRole("navigation");
  });

  it("hides signoff section if experiment is launched", async () => {
    // this table is shown in the Summary component instead
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(
        screen.queryByTestId("summary-page-signoff"),
      ).not.toBeInTheDocument();
    });
  });

  it("displays a banner for pages missing fields required for review", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      readyForReview: {
        ready: false,
        message: {
          channel: [SERVER_ERRORS.EMPTY_LIST],
        },
      },
    });
    render(<Subject mocks={[mock]} />);
    await screen.findByText(/all required fields must be completed/);
    expect(screen.queryByTestId("launch-draft-to-preview")).toBeNull();
  });

  it("indicates status in review", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("in-review-label")).toBeInTheDocument(),
    );
  });

  it("indicates status in preview", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.PREVIEW,
    });
    render(<Subject mocks={[mock]} />);
    await screen.findByTestId("in-preview-label");
  });

  it("handles Launch to Preview from Draft as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.PREVIEW,
      CHANGELOG_MESSAGES.LAUNCHED_TO_PREVIEW,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const launchButton = (await screen.findByTestId(
      "launch-draft-to-preview",
    )) as HTMLButtonElement;
    await act(async () => void fireEvent.click(launchButton));
  });

  it("handles Launch without Preview from Draft as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createFullStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.DRAFT,
      NimbusExperimentStatus.LIVE,
      NimbusExperimentPublishStatus.REVIEW,
      CHANGELOG_MESSAGES.REQUESTED_REVIEW,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    await launchFromDraftToReview();
  });

  it("handles cancelled Launch to Review as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createStatusMutationMock(experiment.id!);
    render(<Subject mocks={[mock, mutationMock]} />);

    const startButton = (await screen.findByTestId(
      "start-launch-draft-to-review",
    )) as HTMLButtonElement;

    fireEvent.click(startButton);

    const cancelButton = await screen.findByTestId("cancel");
    fireEvent.click(cancelButton);
    await screen.findByTestId("launch-draft-to-preview");
  });

  it("handles Launch to Preview after reconsidering Launch to Review from Draft", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.PREVIEW,
      CHANGELOG_MESSAGES.LAUNCHED_TO_PREVIEW,
    );
    render(<Subject mocks={[mock, mutationMock]} />);

    const startButton = (await screen.findByTestId(
      "start-launch-draft-to-review",
    )) as HTMLButtonElement;
    fireEvent.click(startButton);

    const launchButton = (await screen.findByTestId(
      "launch-to-preview-instead",
    )) as HTMLButtonElement;
    fireEvent.click(launchButton);
  });

  it("handles Back to Draft from Preview", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.PREVIEW,
    });
    const mutationMock = createStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.DRAFT,
      CHANGELOG_MESSAGES.RETURNED_TO_DRAFT,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const launchButton = (await screen.findByTestId(
      "launch-preview-to-draft",
    )) as HTMLButtonElement;
    await act(async () => void fireEvent.click(launchButton));
  });

  it("handles approval of launch as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      ...reviewRequestedBaseProps,
      canReview: true,
    });
    const mutationMock = createFullStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.DRAFT,
      NimbusExperimentStatus.LIVE,
      NimbusExperimentPublishStatus.APPROVED,
      CHANGELOG_MESSAGES.REVIEW_APPROVED,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const approveButton = await screen.findByTestId("approve-request");
    expect(approveButton).toHaveTextContent("Approve and Launch Experiment");
    fireEvent.click(approveButton);
    const openRemoteSettingsButton = await screen.findByTestId(
      "open-remote-settings",
    );
    expect(openRemoteSettingsButton).toHaveProperty(
      "href",
      experiment.reviewUrl,
    );
  });

  it("handles rejection of launch as expected", async () => {
    const expectedReason = "This smells bad.";
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      ...reviewRequestedBaseProps,
      canReview: true,
    });
    const mutationMock = createFullStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.DRAFT,
      null,
      NimbusExperimentPublishStatus.IDLE,
      expectedReason,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    await screen.findByText("Approve and Launch Experiment");
    const rejectButton = await screen.findByTestId("reject-request");
    fireEvent.click(rejectButton);
    const rejectSubmitButton = await screen.findByTestId("reject-submit");
    const rejectReasonField = await screen.findByTestId("reject-reason");
    fireEvent.change(rejectReasonField, {
      target: { value: expectedReason },
    });
    fireEvent.blur(rejectReasonField);
    fireEvent.click(rejectSubmitButton);
  });

  it("handles submission with server API error", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createStatusMutationMock(experiment.id!);
    mutationMock.result.errors = [new Error("Boo")];
    render(<Subject mocks={[mock, mutationMock]} />);
    await launchFromDraftToReview();
    await waitFor(() =>
      expect(screen.getByTestId("submit-error")).toBeInTheDocument(),
    );
  });

  it("handles submission with server-side validation errors", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    const mutationMock = createFullStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatus.DRAFT,
      NimbusExperimentStatus.LIVE,
      NimbusExperimentPublishStatus.REVIEW,
      CHANGELOG_MESSAGES.REQUESTED_REVIEW,
    );
    const errorMessage = "Something went very wrong.";
    mutationMock.result.data.updateExperiment.message = {
      status: [errorMessage],
    };
    render(<Subject mocks={[mock, mutationMock]} />);
    await launchFromDraftToReview();
    await waitFor(() => {
      expect(screen.getByTestId("submit-error")).toBeInTheDocument();
      expect(screen.getByTestId("submit-error")).toHaveTextContent(
        errorMessage,
      );
    });
  });

  it("handles rejection of end as expected", async () => {
    const expectedReason = "This smells bad.";
    const { experiment, mock } = mockExperimentQuery("demo-slug", {
      ...endReviewRequestedBaseProps,
      canReview: true,
    });
    const mutationMock = createMutationMock(
      experiment.id!,
      NimbusExperimentPublishStatus.IDLE,
      { statusNext: null, changelogMessage: expectedReason },
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const rejectButton = await screen.findByTestId("reject-request");
    await screen.findByText("Approve and End Experiment");
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

  it("handles approval of end as expected", async () => {
    const { experiment, mock } = mockExperimentQuery("demo-slug", {
      ...endReviewRequestedBaseProps,
      canReview: true,
    });
    const mutationMock = createMutationMock(
      experiment.id!,
      NimbusExperimentPublishStatus.APPROVED,
      { changelogMessage: CHANGELOG_MESSAGES.END_APPROVED },
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const approveButton = await screen.findByTestId("approve-request");
    expect(approveButton).toHaveTextContent("Approve and End Experiment");
    fireEvent.click(approveButton);
    const openRemoteSettingsButton = await screen.findByTestId(
      "open-remote-settings",
    );
    fireEvent.click(openRemoteSettingsButton);
    expect(openRemoteSettingsButton).toHaveProperty(
      "href",
      experiment.reviewUrl,
    );
  });

  it("handles rejection of end enrollment as expected", async () => {
    const expectedReason = "Enroll more people first, yo.";
    const { experiment, mock } = mockExperimentQuery("demo-slug", {
      ...enrollmentPauseReviewRequestedBaseProps,
      canReview: true,
    });
    const mutationMock = createMutationMock(
      experiment.id!,
      NimbusExperimentPublishStatus.IDLE,
      { statusNext: null, changelogMessage: expectedReason },
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const rejectButton = await screen.findByTestId("reject-request");
    await screen.findByText("Approve and End Enrollment for Experiment");
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

  it("handles approval of end enrollment as expected", async () => {
    const { experiment, mock } = mockExperimentQuery("demo-slug", {
      ...enrollmentPauseReviewRequestedBaseProps,
      canReview: true,
    });
    const mutationMock = createMutationMock(
      experiment.id!,
      NimbusExperimentPublishStatus.APPROVED,
      { changelogMessage: CHANGELOG_MESSAGES.END_APPROVED },
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const approveButton = await screen.findByTestId("approve-request");
    await screen.findByText("Approve and End Enrollment for Experiment");
    fireEvent.click(approveButton);
    const openRemoteSettingsButton = await screen.findByTestId(
      "open-remote-settings",
    );
    fireEvent.click(openRemoteSettingsButton);
    expect(openRemoteSettingsButton).toHaveProperty(
      "href",
      experiment.reviewUrl,
    );
  });

  async function launchFromDraftToReview() {
    const startButton = (await screen.findByTestId(
      "start-launch-draft-to-review",
    )) as HTMLButtonElement;

    await act(async () => void fireEvent.click(startButton));

    const submitButton = await screen.findByTestId("launch-draft-to-review");

    expect(submitButton!).toBeDisabled();
    await checkRequiredBoxes();
    expect(submitButton!).toBeEnabled();

    await act(async () => void fireEvent.click(submitButton));
  }

  it("will not allow submitting if already in review", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      publishStatus: NimbusExperimentPublishStatus.APPROVED,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("in-review-label")).toBeInTheDocument(),
    );
  });
});
