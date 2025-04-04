/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import React from "react";
import {
  BaseSubject,
  MOCK_EXPERIMENT,
  MOCK_LIVE_ROLLOUT,
  reviewApprovedAfterTimeoutBaseProps,
  reviewPendingInRemoteSettingsBaseProps,
  reviewRejectedBaseProps,
  reviewRequestedAfterRejectionBaseProps,
  reviewRequestedBaseProps,
  reviewTimedOutBaseProps,
  REVIEW_URL,
} from "src/components/ChangeApprovalOperations/mocks";
import { LIFECYCLE_REVIEW_FLOWS } from "src/lib/constants";
import { getStatus } from "src/lib/experiment";
import { NimbusExperimentStatusEnum } from "src/types/globalTypes";

const Subject = ({
  rejectChange = () => {},
  approveChange = () => {},
  ...props
}: React.ComponentProps<typeof BaseSubject>) => (
  <BaseSubject
    {...{
      rejectChange,
      approveChange,
      ...props,
    }}
  />
);

describe("ChangeApprovalOperations", () => {
  it("renders as expected", async () => {
    render(<Subject />);
    await screen.findByTestId("action-button");
  });

  it("displays an invalid pages warning when details are missing", async () => {
    const expectedInvalidPages = "overview, thingy, and frobnitz";
    render(
      <Subject
        {...{
          ...reviewRequestedBaseProps,
          canReview: true,
          invalidPages: ["overview", "thingy", "frobnitz"],
          InvalidPagesList: () => <span>{expectedInvalidPages}</span>,
          ready: false,
        }}
      />,
    );
    const invalidPagesAlert = screen.getByTestId("invalid-pages");
    expect(invalidPagesAlert!.textContent).toContain(expectedInvalidPages);
  });

  it("displays an error when ready is false but no pages contain errors", async () => {
    render(
      <Subject
        {...{
          ...reviewRequestedBaseProps,
          canReview: true,
          invalidPages: [],
          InvalidPagesList: undefined,
          ready: false,
        }}
      />,
    );
    screen.getByTestId("invalid-internal-error");
  });

  it("does not display an invalid pages warning when details are missing from an archived experiment", async () => {
    const expectedInvalidPages = "overview, thingy, and frobnitz";
    render(
      <Subject
        {...{
          ...reviewRequestedBaseProps,
          status: {
            ...getStatus(MOCK_EXPERIMENT),
            archived: true,
            draft: true,
          },
          canReview: true,
          invalidPages: ["overview", "thingy", "frobnitz"],
          InvalidPagesList: () => <span>{expectedInvalidPages}</span>,
        }}
      />,
    );
    const invalidPagesAlert = screen.queryByTestId("invalid-pages");
    expect(invalidPagesAlert).not.toBeInTheDocument();
  });

  it("when user can review, supports approval and opening remote settings", async () => {
    const approveChange = jest.fn();
    render(
      <Subject
        {...{
          ...reviewRequestedBaseProps,
          canReview: true,
          approveChange,
        }}
      />,
    );
    const reviewAlertTitle = await screen.findByTestId("review-request-alert");
    await waitFor(() => {
      expect(reviewAlertTitle).toBeInTheDocument();
    });
    const approveButton = await screen.findByTestId("approve-request");
    fireEvent.click(approveButton);
    await waitFor(() => {
      expect(approveChange).toHaveBeenCalled();
    });
    const openRemoteSettingsButton = await screen.findByTestId(
      "open-remote-settings",
    );
    expect(openRemoteSettingsButton).toHaveProperty("href", REVIEW_URL);
  });

  it("when user can review for live updates, supports approval and opening remote settings", async () => {
    const approveChange = jest.fn();
    render(
      <Subject
        {...{
          ...reviewRequestedBaseProps,
          canReview: true,
          approveChange,
          status: {
            ...getStatus(MOCK_LIVE_ROLLOUT),
            draft: false,
            dirty: true,
            live: true,
          },
        }}
      />,
    );
    const reviewAlertTitle = await screen.findByTestId("review-request-alert");
    await waitFor(() => {
      expect(reviewAlertTitle).toBeInTheDocument();
    });

    const approveButton = await screen.findByTestId("approve-request");
    fireEvent.click(approveButton);

    await waitFor(() => {
      expect(approveChange).toHaveBeenCalled();
    });

    const openRemoteSettingsButton = await screen.findByTestId(
      "open-remote-settings",
    );
    expect(openRemoteSettingsButton).toHaveProperty("href", REVIEW_URL);
  });

  it("when user cannot review, an approval pending notice is displayed", async () => {
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn(),
      },
    });

    render(
      <Subject
        {...{
          ...reviewRequestedBaseProps,
          canReview: false,
        }}
      />,
    );
    const pendingMessage = await screen.findByTestId("approval-pending");
    expect(screen.queryByTestId("approve-request")).not.toBeInTheDocument();
    expect(screen.queryByTestId("reject-request")).not.toBeInTheDocument();

    const copyLink = within(pendingMessage).getByText("Click here");
    fireEvent.click(copyLink);
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });

  it("when user can review and review has been approved, button to open remote settings is offered", async () => {
    render(
      <Subject
        {...{
          ...reviewPendingInRemoteSettingsBaseProps,
          canReview: true,
        }}
      />,
    );
    const openRemoteSettingsButton = await screen.findByTestId(
      "open-remote-settings",
    );
    expect(openRemoteSettingsButton).toHaveProperty("href", REVIEW_URL);
  });

  it("when user cannot review and review has been approved, an approval pending notice is displayed", async () => {
    render(
      <Subject
        {...{
          ...reviewPendingInRemoteSettingsBaseProps,
          canReview: false,
        }}
      />,
    );
    await screen.findByTestId("approval-pending");
    expect(
      screen.queryByTestId("open-remote-settings"),
    ).not.toBeInTheDocument();
  });

  it("when user can review, supports rejection and supplying a reason", async () => {
    const expectedReason = "hovercraft contains eels";
    const rejectChange = jest.fn();
    render(
      <Subject
        {...{
          ...reviewRequestedBaseProps,
          canReview: true,
          rejectChange,
        }}
      />,
    );
    const rejectButton = await screen.findByTestId("reject-request");
    fireEvent.click(rejectButton);
    const rejectSubmitButton = await screen.findByTestId("reject-submit");
    const rejectReasonField = await screen.findByTestId("reject-reason");
    fireEvent.change(rejectReasonField, {
      target: { value: expectedReason },
    });
    fireEvent.blur(rejectReasonField);
    fireEvent.click(rejectSubmitButton);
    await waitFor(() => {
      expect(rejectChange).toBeCalledWith(null, {
        changelogMessage: expectedReason,
      });
    });
  });

  it("when user can review, supports rejection and cancelling", async () => {
    const rejectChange = jest.fn();
    render(
      <Subject
        {...{
          ...reviewRequestedBaseProps,
          canReview: true,
          rejectChange,
        }}
      />,
    );
    const rejectButton = await screen.findByTestId("reject-request");
    fireEvent.click(rejectButton);
    const rejectCancelButton = await screen.findByTestId("reject-cancel");
    fireEvent.click(rejectCancelButton);
    await screen.findByTestId("approve-request");
    await screen.findByTestId("reject-request");
    expect(screen.queryByTestId("reject-reason")).not.toBeInTheDocument();
    expect(rejectChange).not.toHaveBeenCalled();
  });

  const commonRejectionCase =
    (
      actionDescription: string,
      oldStatus: NimbusExperimentStatusEnum,
      oldStatusNext: NimbusExperimentStatusEnum,
    ) =>
    async () => {
      const rejectionEvent = {
        ...reviewRejectedBaseProps.rejectionEvent!,
        oldStatus,
        oldStatusNext,
      };
      const { changedBy: rejectionUser, message: rejectionMessage } =
        rejectionEvent;
      render(
        <Subject
          {...{
            ...reviewRejectedBaseProps,
            rejectionEvent,
            actionDescription,
          }}
        />,
      );
      await screen.findByTestId("action-button");
      await screen.findByText(`The request to ${actionDescription} was`, {
        exact: false,
      });
      await screen.findByText(rejectionMessage!, { exact: false });
      await screen.findByText(rejectionUser!.email, { exact: false });
    };

  it(
    "reports a rejection reason when launch review is rejected",
    commonRejectionCase(
      LIFECYCLE_REVIEW_FLOWS.LAUNCH.description,
      NimbusExperimentStatusEnum.DRAFT,
      NimbusExperimentStatusEnum.LIVE,
    ),
  );

  it(
    "reports a rejection reason when end enrollment review is rejected",
    commonRejectionCase(
      LIFECYCLE_REVIEW_FLOWS.PAUSE.description,
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentStatusEnum.LIVE,
    ),
  );

  it(
    "reports a rejection reason when end experiment review is rejected",
    commonRejectionCase(
      LIFECYCLE_REVIEW_FLOWS.END.description,
      NimbusExperimentStatusEnum.LIVE,
      NimbusExperimentStatusEnum.COMPLETE,
    ),
  );

  it("when user can review and review has timed out, a timeout notice is displayed", async () => {
    render(
      <Subject
        {...{
          ...reviewTimedOutBaseProps,
          canReview: true,
        }}
      />,
    );
    await screen.findByTestId("timeout-notice");
    await screen.findByTestId("approve-request");
    await screen.findByTestId("reject-request");
  });

  it("when user can review and review has timed out, a timeout notice is displayed", async () => {
    render(
      <Subject
        {...{
          ...reviewTimedOutBaseProps,
          canReview: false,
        }}
      />,
    );
    await screen.findByTestId("approval-pending");
    expect(screen.queryByTestId("timeout-notice")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approve-request")).not.toBeInTheDocument();
    expect(screen.queryByTestId("reject-request")).not.toBeInTheDocument();
  });

  it("supports a follow-up review request after a rejection", async () => {
    render(
      <Subject
        {...{
          ...reviewRequestedAfterRejectionBaseProps,
          canReview: true,
        }}
      />,
    );
    await screen.findByTestId("approve-request");
  });

  it("supports a retried approval after a timeout", async () => {
    render(
      <Subject
        {...{
          ...reviewApprovedAfterTimeoutBaseProps,
          canReview: true,
        }}
      />,
    );
    await screen.findByTestId("open-remote-settings");
  });
});
