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
import {
  createFullStatusMutationMock,
  createStatusMutationMock,
  endReviewRequestedBaseProps,
  enrollmentPauseReviewRequestedBaseProps,
  reviewRequestedBaseProps,
  Subject,
  updateReviewRequestedBaseProps,
} from "src/components/PageSummary/mocks";
import { createMutationMock } from "src/components/Summary/mocks";
import {
  AUDIENCE_OVERLAP_WARNINGS,
  CHANGELOG_MESSAGES,
  QA_STATUS_PROPERTIES,
  SERVER_ERRORS,
} from "src/lib/constants";
import { mockExperimentQuery, mockLiveRolloutQuery } from "src/lib/mocks";
import {
  NimbusExperimentApplicationEnum,
  NimbusExperimentChannelEnum,
  NimbusExperimentFirefoxVersionEnum,
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentQAStatusEnum,
  NimbusExperimentStatusEnum,
} from "src/types/globalTypes";

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
    expect(screen.getByTestId("summary-timeline")).toBeInTheDocument();

    screen.getByRole("navigation");
  });

  it("renders without launch controls when archived", async () => {
    const { mock } = mockExperimentQuery("demo-slug", { isArchived: true });
    render(<Subject mocks={[mock]} />);
    await screen.findByTestId("PageSummary");
    expect(
      screen.queryByTestId("start-launch-draft-to-review"),
    ).not.toBeInTheDocument();
  });

  it("renders the cancel review button if the experiment is in review state", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      ...reviewRequestedBaseProps,
      canReview: true,
    });
    render(<Subject mocks={[mock]} />);
    await screen.findByText("Cancel Review");
  });

  it("verify cancel review doesn't change enrollment days", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.LIVE,
      publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
    });
    const mutationMock = createMutationMock(
      experiment.id!,
      NimbusExperimentPublishStatusEnum.IDLE,
      {
        statusNext: NimbusExperimentStatusEnum.LIVE,
        changelogMessage: CHANGELOG_MESSAGES.CANCEL_REVIEW,
        isEnrollmentPaused: false,
      },
    );
    render(<Subject mocks={[mock, mutationMock]} />);

    await screen.findByTestId("cancel-review-start");
    fireEvent.click(screen.getByTestId("cancel-review-start"));
    await waitFor(() => {
      expect(screen.queryByTestId("submit-error")).not.toBeInTheDocument();
    });
    expect(screen.queryByTestId("label-enrollment-days")).toHaveTextContent(
      "1 day",
    );
  });

  it("can cancel review when the experiment is in the review state", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      ...reviewRequestedBaseProps,
      canReview: true,
    });
    const mutationMock = createFullStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatusEnum.DRAFT,
      null,
      NimbusExperimentPublishStatusEnum.IDLE,
      CHANGELOG_MESSAGES.CANCEL_REVIEW,
    );
    render(<Subject mocks={[mock, mutationMock]} />);

    await screen.findByTestId("cancel-review-start");
    fireEvent.click(screen.getByTestId("cancel-review-start"));
    await waitFor(() => {
      expect(screen.queryByTestId("submit-error")).not.toBeInTheDocument();
    });
  });

  it("can cancel review when dirty rollout is in the review state", async () => {
    const { mockRollout, rollout } = mockLiveRolloutQuery("demo-slug", {
      ...reviewRequestedBaseProps,
      canReview: true,
      isRolloutDirty: true,
    });
    const mutationMock = createFullStatusMutationMock(
      rollout.id!,
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentPublishStatusEnum.REVIEW,
      CHANGELOG_MESSAGES.CANCEL_REVIEW,
    );
    render(<Subject mocks={[mockRollout, mutationMock]} />);

    await screen.findByTestId("cancel-review-start");
    fireEvent.click(screen.getByTestId("cancel-review-start"));

    screen.queryByTestId("pill-dirty-unpublished");
    screen.queryByTestId("update-live-to-review");
  });

  it("can reject ending when dirty rollout is in the review state", async () => {
    const { mockRollout, rollout } = mockLiveRolloutQuery("demo-slug", {
      ...reviewRequestedBaseProps,
      canReview: true,
      isRolloutDirty: true,
    });
    const mutationMock = createFullStatusMutationMock(
      rollout.id!,
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentStatusEnum.COMPLETE,
      NimbusExperimentPublishStatusEnum.REVIEW,
      CHANGELOG_MESSAGES.CANCEL_REVIEW,
    );
    render(<Subject mocks={[mockRollout, mutationMock]} />);

    screen.queryByTestId("pill-dirty-unpublished");

    fireEvent.click(screen.getByTestId("reject-request"));

    screen.queryByTestId("pill-dirty-unpublished");
    screen.queryByTestId("update-live-to-review");
  });

  it("hides takeaways section if experiment is not complete", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.DRAFT,
    });
    render(<Subject mocks={[mock]} />);
    await screen.findByTestId("PageSummary");
    expect(screen.queryByTestId("Takeaways")).not.toBeInTheDocument();
  });

  it("reveals takeaways section if experiment is complete", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.COMPLETE,
    });
    render(<Subject mocks={[mock]} />);
    await screen.findByTestId("PageSummary");
    expect(screen.queryByTestId("Takeaways")).toBeInTheDocument();
  });

  it("displays a banner for pages missing fields required for review", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      readyForReview: {
        ready: false,
        message: {
          channel: [SERVER_ERRORS.EMPTY_LIST],
        },
        warnings: {},
      },
    });
    render(<Subject mocks={[mock]} />);
    await screen.findByText(/all required fields must be completed/);
    expect(screen.queryByTestId("launch-draft-to-preview")).toBeNull();
  });

  it("indicates status in review", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("in-review-label")).toBeInTheDocument(),
    );
  });

  it("indicates status in preview", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.PREVIEW,
    });
    render(<Subject mocks={[mock]} />);
    await screen.findByTestId("in-preview-label");
  });

  it("handles Launch to Preview from Draft as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.DRAFT,
    });
    const mutationMock = createStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatusEnum.PREVIEW,
      CHANGELOG_MESSAGES.LAUNCHED_TO_PREVIEW,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const launchButton = (await screen.findByTestId(
      "launch-draft-to-preview",
    )) as HTMLButtonElement;
    await act(async () => void fireEvent.click(launchButton));
  });

  it("prevents launching to preview for experiments that cannot", async () => {
    const { mock, experiment } = mockExperimentQuery("slug", {
      canPublishToPreview: false,
    });

    render(<Subject mocks={[mock]} />);

    expect(screen.queryByTestId("launch-to-preview-instead")).toBeNull();

    screen.getByTestId("cannot-launch-to-preview");
  });

  it("handles Launch without Preview from Draft as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.DRAFT,
    });
    const mutationMock = createFullStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatusEnum.DRAFT,
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentPublishStatusEnum.REVIEW,
      CHANGELOG_MESSAGES.REQUESTED_REVIEW,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    await launchFromDraftToReview();
  });

  it("handles cancelled Launch to Review as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.DRAFT,
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
      status: NimbusExperimentStatusEnum.DRAFT,
    });
    const mutationMock = createStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatusEnum.PREVIEW,
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
      status: NimbusExperimentStatusEnum.PREVIEW,
    });
    const mutationMock = createStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatusEnum.DRAFT,
      CHANGELOG_MESSAGES.RETURNED_TO_DRAFT,
    );
    render(<Subject mocks={[mock, mutationMock]} />);
    const launchButton = (await screen.findByTestId(
      "launch-preview-to-draft",
    )) as HTMLButtonElement;
    await act(async () => void fireEvent.click(launchButton));
  });

  it("can go back to Draft from Preview with invalid experiment info", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.PREVIEW,
      readyForReview: {
        ready: false,
        message: {
          targeting_config_slug: [
            '"urlbar_firefox_suggest_us_en" is not a valid choice.',
          ],
        },
        warnings: {},
      },
    });
    render(<Subject mocks={[mock]} />);
    await screen.findByTestId("launch-preview-to-draft");
  });

  it("handles approval of launch as expected", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      ...reviewRequestedBaseProps,
      canReview: true,
    });
    const mutationMock = createFullStatusMutationMock(
      experiment.id!,
      NimbusExperimentStatusEnum.DRAFT,
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentPublishStatusEnum.APPROVED,
      CHANGELOG_MESSAGES.REVIEW_APPROVED,
    );
    render(<Subject mocks={[mock, mock, mutationMock]} />);
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
      NimbusExperimentStatusEnum.DRAFT,
      null,
      NimbusExperimentPublishStatusEnum.REVIEW,
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

    await waitFor(() =>
      expect(screen.queryByTestId("submit-error")).not.toBeInTheDocument(),
    );
  });

  it("handles approval of live update as expected", async () => {
    const { mockRollout, rollout } = mockLiveRolloutQuery("demo-slug", {
      ...updateReviewRequestedBaseProps,
      canReview: true,
      isRolloutDirty: true,
    });
    const mutationMock = createFullStatusMutationMock(
      rollout.id!,
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentPublishStatusEnum.APPROVED,
      CHANGELOG_MESSAGES.REVIEW_APPROVED_UPDATE,
    );
    render(<Subject mocks={[mockRollout, mockRollout, mutationMock]} />);
    const approveButton = await screen.findByTestId("approve-request");
    expect(approveButton).toHaveTextContent("Approve and Update Rollout");
    fireEvent.click(approveButton);
    const openRemoteSettingsButton = await screen.findByTestId(
      "open-remote-settings",
    );
    expect(openRemoteSettingsButton).toHaveProperty("href", rollout.reviewUrl);
  });

  it("handles rejection of live update as expected", async () => {
    const expectedReason = "Oh no.";
    const { mockRollout, rollout } = mockLiveRolloutQuery("demo-slug", {
      ...updateReviewRequestedBaseProps,
      canReview: true,
      isRolloutDirty: true,
    });
    const mutationMock = createFullStatusMutationMock(
      rollout.id!,
      NimbusExperimentStatusEnum.LIVE,
      null,
      NimbusExperimentPublishStatusEnum.IDLE,
      expectedReason,
    );
    render(<Subject mocks={[mockRollout, mutationMock]} />);
    await screen.findByText("Approve and Update Rollout");

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

  it("handles submission with server API error", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.DRAFT,
    });
    const mutationMock = createStatusMutationMock(experiment.id!);
    mutationMock.result.errors = [new Error("Boo")];
    render(<Subject mocks={[mock, mutationMock]} />);
    await launchFromDraftToReview();
    await waitFor(() => screen.getByTestId("submit-error-warning"));
  });

  // TODO: #6802
  // it("handles submission with server-side validation errors", async () => {
  //   const { mock, experiment } = mockExperimentQuery("demo-slug", {
  //     status: NimbusExperimentStatusEnum.DRAFT,
  //   });
  //   const mutationMock = createFullStatusMutationMock(
  //     experiment.id!,
  //     NimbusExperimentStatusEnum.DRAFT,
  //     NimbusExperimentStatusEnum.LIVE,
  //     NimbusExperimentPublishStatusEnum.REVIEW,
  //     CHANGELOG_MESSAGES.REQUESTED_REVIEW,
  //   );
  //   const errorMessage = "Something went very wrong.";
  //   mutationMock.result.data.updateExperiment.message = {
  //     status: [errorMessage],
  //   };
  //   render(<Subject mocks={[mock, mutationMock]} />);
  //   await launchFromDraftToReview();
  //   await waitFor(() => {
  //     expect(screen.getByTestId("submit-error")).toBeInTheDocument();
  //     expect(screen.getByTestId("submit-error")).toHaveTextContent(
  //       errorMessage,
  //     );
  //   });
  // });

  it("handles rejection of end as expected", async () => {
    const expectedReason = "This smells bad.";
    const { experiment, mock } = mockExperimentQuery("demo-slug", {
      ...endReviewRequestedBaseProps,
      canReview: true,
    });
    const mutationMock = createMutationMock(
      experiment.id!,
      NimbusExperimentPublishStatusEnum.IDLE,
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
      NimbusExperimentPublishStatusEnum.APPROVED,
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
      NimbusExperimentPublishStatusEnum.IDLE,
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
      NimbusExperimentPublishStatusEnum.APPROVED,
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
      publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.getByTestId("in-review-label")).toBeInTheDocument(),
    );
  });

  it("will not allow submitting live update if already in review", async () => {
    const { mockRollout } = mockLiveRolloutQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.LIVE,
      publishStatus: NimbusExperimentPublishStatusEnum.APPROVED,
      isRolloutDirty: true,
    });
    render(<Subject mocks={[mockRollout]} />);
    await waitFor(() =>
      expect(screen.getByTestId("in-review-label")).toBeInTheDocument(),
    );
    await waitFor(() =>
      expect(screen.queryByTestId("approve-request")).not.toBeInTheDocument(),
    );
  });

  it("renders enrollment complete badge if enrollment is not paused", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.LIVE,
      isEnrollmentPaused: true,
      enrollmentEndDate: new Date().toISOString(),
    });
    const mutationMock = createStatusMutationMock(experiment.id!);
    render(<Subject mocks={[mock, mutationMock]} />);
    await screen.findByTestId("pill-enrolling-complete");
  });

  it("renders enrollment active badge if enrollment is not paused", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.LIVE,
      isEnrollmentPaused: false,
    });
    const mutationMock = createStatusMutationMock(experiment.id!);
    render(<Subject mocks={[mock, mutationMock]} />);
    await screen.findByTestId("pill-enrolling-active");
  });

  it.each([
    [
      NimbusExperimentStatusEnum.LIVE,
      null,
      NimbusExperimentPublishStatusEnum.IDLE,
      NimbusExperimentPublishStatusEnum.IDLE,
    ],
    [
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentPublishStatusEnum.IDLE,
      NimbusExperimentPublishStatusEnum.REVIEW,
    ],
  ])(
    "renders unpublished changes status pill when live update",
    async (
      status: NimbusExperimentStatusEnum,
      statusNext: NimbusExperimentStatusEnum | null,
      publishStatus: NimbusExperimentPublishStatusEnum,
      mutationPublishStatus: NimbusExperimentPublishStatusEnum,
    ) => {
      const { mockRollout, rollout } = mockLiveRolloutQuery("demo-slug", {
        status: status,
        publishStatus: publishStatus,
        statusNext: null,
        isRollout: true,
        isEnrollmentPaused: false,
        isRolloutDirty: true,
      });
      const mutationMock = createFullStatusMutationMock(
        rollout.id!,
        status,
        statusNext,
        mutationPublishStatus,
        CHANGELOG_MESSAGES.REQUESTED_REVIEW,
      );
      render(<Subject mocks={[mockRollout, mutationMock]} />);

      expect(
        screen.queryByTestId("pill-dirty-unpublished"),
      ).toBeInTheDocument();
    },
  );

  it.each([
    [
      NimbusExperimentQAStatusEnum.GREEN,
      QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.GREEN].description,
    ],
    [
      NimbusExperimentQAStatusEnum.YELLOW,
      QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.YELLOW].description,
    ],
    [
      NimbusExperimentQAStatusEnum.RED,
      QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.RED].description,
    ],
  ])(
    "renders qa status pill for each qa status",
    async (qaStatus: NimbusExperimentQAStatusEnum, qaLabel: string) => {
      const { mock } = mockExperimentQuery("demo-slug", {
        status: NimbusExperimentStatusEnum.LIVE,
        publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
        qaStatus: qaStatus,
        statusNext: null,
      });

      render(<Subject mocks={[mock]} />);
      const qaStatusPill = await screen.findByTestId("pill-qa-status");
      expect(qaStatusPill).toBeInTheDocument();
      expect(qaStatusPill).toHaveTextContent(qaLabel);
    },
  );

  it("does not render qa status pill when QA status is not set", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.LIVE,
      publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
      qaStatus: NimbusExperimentQAStatusEnum.NOT_SET,
      statusNext: null,
    });

    render(<Subject mocks={[mock]} />);
    expect(screen.queryByTestId("pill-qa-status")).not.toBeInTheDocument();
  });

  it.each([
    [NimbusExperimentStatusEnum.DRAFT],
    [NimbusExperimentStatusEnum.LIVE],
    [NimbusExperimentStatusEnum.PREVIEW],
    [NimbusExperimentStatusEnum.COMPLETE],
  ])(
    "renders qa status pill for each status",
    async (experimentStatus: NimbusExperimentStatusEnum) => {
      const { mock } = mockExperimentQuery("demo-slug", {
        status: experimentStatus,
        publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
        qaStatus: NimbusExperimentQAStatusEnum.GREEN,
        statusNext: null,
      });

      render(<Subject mocks={[mock]} />);
      const qaStatusPill = await screen.findByTestId("pill-qa-status");
      expect(qaStatusPill).toBeInTheDocument();
      expect(qaStatusPill).toHaveTextContent(
        QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.GREEN].description,
      );
    },
  );

  it("renders qa status pill when archived", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.COMPLETE,
      publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
      qaStatus: NimbusExperimentQAStatusEnum.GREEN,
      statusNext: null,
      isArchived: true,
    });

    render(<Subject mocks={[mock]} />);
    const qaStatusPill = await screen.findByTestId("pill-qa-status");
    expect(qaStatusPill).toBeInTheDocument();
    expect(qaStatusPill).toHaveTextContent(
      QA_STATUS_PROPERTIES[NimbusExperimentQAStatusEnum.GREEN].description,
    );
  });

  it("will not render qa status pill when status is not set", async () => {
    const { mock, experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatusEnum.LIVE,
      publishStatus: NimbusExperimentPublishStatusEnum.IDLE,
      statusNext: null,
    });
    render(<Subject mocks={[mock]} />);
    expect(screen.queryByTestId("pill-qa-status")).not.toBeInTheDocument();
  });

  it.each([
    [
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentPublishStatusEnum.REVIEW,
      NimbusExperimentPublishStatusEnum.APPROVED,
    ],
    [
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentPublishStatusEnum.APPROVED,
      NimbusExperimentPublishStatusEnum.WAITING,
    ],
  ])(
    "renders unpublished changes status pill when live update reviews",
    async (
      liveStatus: NimbusExperimentStatusEnum,
      publishStatus: NimbusExperimentPublishStatusEnum,
      mutationPublishStatus: NimbusExperimentPublishStatusEnum,
    ) => {
      const { mockRollout, rollout } = mockLiveRolloutQuery("demo-slug", {
        status: liveStatus,
        publishStatus: publishStatus,
        statusNext: liveStatus,
        isRollout: true,
        isEnrollmentPaused: false,
        isRolloutDirty: true,
      });
      const mutationMock = createFullStatusMutationMock(
        rollout.id!,
        liveStatus,
        liveStatus,
        mutationPublishStatus,
        CHANGELOG_MESSAGES.REQUESTED_REVIEW,
      );
      render(<Subject mocks={[mockRollout, mutationMock]} />);

      expect(
        screen.queryByTestId("pill-dirty-unpublished"),
      ).toBeInTheDocument();
    },
  );

  it.each([
    [
      NimbusExperimentStatusEnum.DRAFT,
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentPublishStatusEnum.REVIEW,
      NimbusExperimentPublishStatusEnum.APPROVED,
    ],
    [
      NimbusExperimentStatusEnum.DRAFT,
      null,
      NimbusExperimentPublishStatusEnum.IDLE,
      NimbusExperimentPublishStatusEnum.IDLE,
    ],
    [
      NimbusExperimentStatusEnum.LIVE,
      null,
      NimbusExperimentPublishStatusEnum.IDLE,
      NimbusExperimentPublishStatusEnum.IDLE,
    ],
  ])(
    "does not render unpublished changes status pill when not live update",
    async (
      status: NimbusExperimentStatusEnum,
      statusNext: NimbusExperimentStatusEnum | null,
      publishStatus: NimbusExperimentPublishStatusEnum,
      mutationPublishStatus: NimbusExperimentPublishStatusEnum,
    ) => {
      const { mock, experiment } = mockExperimentQuery("demo-slug", {
        status: status,
        publishStatus: publishStatus,
        statusNext: null,
        isRollout: false,
        isEnrollmentPaused: false,
      });
      const mutationMock = createFullStatusMutationMock(
        experiment.id!,
        status,
        statusNext,
        mutationPublishStatus,
        CHANGELOG_MESSAGES.REQUESTED_REVIEW,
      );
      render(<Subject mocks={[mock, mutationMock]} />);

      expect(
        screen.queryByTestId("pill-dirty-unpublished"),
      ).not.toBeInTheDocument();
    },
  );
});

describe("PageSummary Warnings", () => {
  it("displays a warning for rollouts that will be in the same bucket", async () => {
    const BUCKET_WARNING =
      "A rollout already exists for this combination of rollout, ...";
    const { mock } = mockExperimentQuery("demo-slug", {
      readyForReview: {
        ready: true,
        message: {},
        warnings: {
          bucketing: [BUCKET_WARNING],
        },
      },
      isRollout: true,
      application: NimbusExperimentApplicationEnum.DESKTOP,
      firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_106,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      targetingConfigSlug: "OH_NO",
    });
    render(<Subject mocks={[mock]} />);
    screen.getByTestId("bucketing-warning");
  });

  it("displays no duplicate rollout warning for experiments", async () => {
    const BUCKET_WARNING =
      "A rollout already exists for this combination of rollout, ...";
    const { mock } = mockExperimentQuery("demo-slug", {
      readyForReview: {
        ready: true,
        message: {},
        warnings: {
          bucketing: [BUCKET_WARNING],
        },
      },
      isRollout: false,
      application: NimbusExperimentApplicationEnum.DESKTOP,
      firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_106,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      targetingConfigSlug: "OH_NO",
    });
    render(<Subject mocks={[mock]} />);
    expect(screen.queryByTestId("bucketing-warning")).toBeNull();
  });

  it("displays a warning for desktop rollouts under v114", async () => {
    const WARNING = "WARNING: Decreasing the population size while live";
    const { mockRollout } = mockLiveRolloutQuery("demo-slug", {
      readyForReview: {
        ready: true,
        message: {},
        warnings: {
          firefox_min_version: [WARNING],
        },
      },
      isRollout: true,
      application: NimbusExperimentApplicationEnum.DESKTOP,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      targetingConfigSlug: "OH_NO",
    });
    render(<Subject mocks={[mockRollout]} />);
    await waitFor(() => screen.queryByTestId("desktop-min-version-warning"));
  });

  it("displays no warning for desktop rollouts above v113", async () => {
    const { mockRollout } = mockLiveRolloutQuery("demo-slug", {
      readyForReview: {
        ready: true,
        message: {},
        warnings: {},
      },
      isRollout: true,
      application: NimbusExperimentApplicationEnum.DESKTOP,
      firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_116,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      targetingConfigSlug: "OH_NO",
    });
    render(<Subject mocks={[mockRollout]} />);
    expect(screen.queryByTestId("desktop-min-version-warning")).toBeNull();
  });

  it("displays no min version warning for non-desktop rollouts", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      readyForReview: {
        ready: true,
        message: {},
        warnings: {},
      },
      isRollout: true,
      application: NimbusExperimentApplicationEnum.FENIX,
      firefoxMinVersion: NimbusExperimentFirefoxVersionEnum.FIREFOX_106,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      targetingConfigSlug: "OH_NO",
    });
    render(<Subject mocks={[mock]} />);
    expect(screen.queryByTestId("desktop-min-version-warning")).toBeNull();
  });

  it("displays rollout setpref warning", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      readyForReview: {
        ready: true,
        message: {},
        warnings: {
          pref_rollout_reenroll: ["uh oh"],
        },
      },
      isRollout: true,
      application: NimbusExperimentApplicationEnum.DESKTOP,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
    });

    render(<Subject mocks={[mock]} />);

    screen.queryByTestId("rollout-setpref-reenroll-warnings");
  });

  it("displays warnings for excluded live experiments audience overlap", async () => {
    const warning = AUDIENCE_OVERLAP_WARNINGS.EXCLUDING_EXPERIMENTS_WARNING;
    const { mock } = mockExperimentQuery("demo-slug", {
      application: NimbusExperimentApplicationEnum.DESKTOP,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      excludedLiveDeliveries: ["my-slimy-slug"],
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.queryByTestId("excluding-live-experiments-warning"));
      expect(screen.getByText("my-slimy-slug")).toBeInTheDocument();
      const excludingTest = screen.findByText(
        (content: string, node: Element | null) =>
          node ? (node.textContent ?? "").includes(warning) : false,
      );
      expect(excludingTest).resolves.toBeInTheDocument();
    });
  });

  it("displays no warning when no excluded live experiments audience overlap", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      application: NimbusExperimentApplicationEnum.DESKTOP,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      excludedLiveDeliveries: [],
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(
        screen.queryByTestId("excluding-live-experiments-warning"),
      ).toBeNull(),
    );
  });

  it("displays warnings for live experiments in bucket audience overlap", async () => {
    const warning = AUDIENCE_OVERLAP_WARNINGS.LIVE_EXPERIMENTS_BUCKET_WARNING;
    const { mock } = mockExperimentQuery("demo-slug", {
      application: NimbusExperimentApplicationEnum.DESKTOP,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      liveExperimentsInNamespace: ["my-slimy-slug"],
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.queryByTestId("live-experiments-in-bucket-warning"));
      expect(screen.getByText("my-slimy-slug")).toBeInTheDocument();
      const bucketTest = screen.findByText(
        (content: string, node: Element | null) =>
          node ? (node.textContent ?? "").includes(warning) : false,
      );
      expect(bucketTest).resolves.toBeInTheDocument();
    });
  });

  it("displays no warning when no live experiments in bucket audience overlap", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      application: NimbusExperimentApplicationEnum.DESKTOP,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      liveExperimentsInNamespace: [],
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(
        screen.queryByTestId("live-experiments-in-bucket-warning"),
      ).toBeNull(),
    );
  });

  it("displays just the multifeature warning when there are multiple audience overlaps", async () => {
    const multifeatureWarning =
      AUDIENCE_OVERLAP_WARNINGS.LIVE_MULTIFEATURE_WARNING;
    const { mock } = mockExperimentQuery("demo-slug", {
      application: NimbusExperimentApplicationEnum.DESKTOP,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      liveExperimentsInNamespace: ["my-slimy-slug"],
      featureHasLiveMultifeatureExperiments: ["my-slimy-slug"],
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(
        screen.queryByTestId("live-experiments-in-bucket-warning"),
      ).toBeNull();
      expect(screen.queryByTestId("live-multifeature-warning"));
      expect(screen.getByText("my-slimy-slug")).toBeInTheDocument();
      const multifeatureTest = screen.findByText(
        (content: string, node: Element | null) =>
          node ? (node.textContent ?? "").includes(multifeatureWarning) : false,
      );
      expect(multifeatureTest).resolves.toBeInTheDocument();
    });
  });

  it("displays warnings for live multifeature audience overlap", async () => {
    const warning = AUDIENCE_OVERLAP_WARNINGS.LIVE_MULTIFEATURE_WARNING;
    const { mock } = mockExperimentQuery("demo-slug", {
      application: NimbusExperimentApplicationEnum.DESKTOP,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      featureHasLiveMultifeatureExperiments: ["my-slimy-slug", "smooth-slug"],
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() => {
      expect(screen.queryByTestId("live-multifeature-warning"));
      expect(screen.getByText("my-slimy-slug")).toBeInTheDocument();
      expect(screen.getByText("smooth-slug")).toBeInTheDocument();
      const multifeatureTest = screen.findByText(
        (content: string, node: Element | null) =>
          node ? (node.textContent ?? "").includes(warning) : false,
      );
      expect(multifeatureTest).resolves.toBeInTheDocument();
    });
  });

  it("displays no warning when no live multifeature audience overlap", async () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      application: NimbusExperimentApplicationEnum.DESKTOP,
      channel: NimbusExperimentChannelEnum.NIGHTLY,
      status: NimbusExperimentStatusEnum.DRAFT,
      featureHasLiveMultifeatureExperiments: [],
    });
    render(<Subject mocks={[mock]} />);
    await waitFor(() =>
      expect(screen.queryByTestId("live-multifeature-warning")).toBeNull(),
    );
  });

  it.each([
    [
      NimbusExperimentStatusEnum.DRAFT,
      NimbusExperimentPublishStatusEnum.IDLE,
      true,
    ],
    [
      NimbusExperimentStatusEnum.DRAFT,
      NimbusExperimentPublishStatusEnum.REVIEW,
      true,
    ],
    [
      NimbusExperimentStatusEnum.PREVIEW,
      NimbusExperimentPublishStatusEnum.IDLE,
      true,
    ],
    [
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentPublishStatusEnum.IDLE,
      false,
    ],
    [
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentPublishStatusEnum.REVIEW,
      false,
    ],
    [
      NimbusExperimentStatusEnum.COMPLETE,
      NimbusExperimentPublishStatusEnum.IDLE,
      false,
    ],
  ])(
    "displays audience overlap warnings in status",
    async (
      status: NimbusExperimentStatusEnum,
      publishStatus: NimbusExperimentPublishStatusEnum,
      displayWarning: boolean,
    ) => {
      const { mock } = mockExperimentQuery("demo-slug", {
        application: NimbusExperimentApplicationEnum.DESKTOP,
        channel: NimbusExperimentChannelEnum.NIGHTLY,
        status: status,
        publishStatus: publishStatus,
        excludedLiveDeliveries: ["my-silly-slug"],
        featureHasLiveMultifeatureExperiments: ["my-slimy-slug"],
        liveExperimentsInNamespace: ["my-scary-slug"],
      });
      render(<Subject mocks={[mock]} />);
      if (displayWarning) {
        await waitFor(() => {
          expect(screen.queryByTestId("excluding-live-experiments-warning"));
          expect(screen.queryByTestId("live-experiments-in-bucket-warning"));
          expect(screen.queryByTestId("live-multifeature-warning"));
        });
      } else {
        await waitFor(() => {
          expect(
            screen.queryByTestId("excluding-live-experiments-warning"),
          ).toBeNull();
          expect(
            screen.queryByTestId("live-experiments-in-bucket-warning"),
          ).toBeNull();
          expect(screen.queryByTestId("live-multifeature-warning")).toBeNull();
        });
      }
    },
  );
});
