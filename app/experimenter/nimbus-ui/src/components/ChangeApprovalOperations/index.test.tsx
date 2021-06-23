/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import {
  BaseSubject,
  reviewApprovedAfterTimeoutBaseProps,
  reviewPendingInRemoteSettingsBaseProps,
  reviewRejectedBaseProps,
  reviewRequestedAfterRejectionBaseProps,
  reviewRequestedBaseProps,
  reviewTimedOutBaseProps,
} from "./mocks";

const REVIEW_URL =
  "http://localhost:8888/v1/admin/#/buckets/main-workspace/collections/nimbus-mobile-experiments/records";

const Subject = ({
  rejectChange = () => {},
  approveChange = () => {},
  reviewUrl = REVIEW_URL,
  ...props
}: React.ComponentProps<typeof BaseSubject>) => (
  <BaseSubject
    {...{
      rejectChange,
      approveChange,
      reviewUrl,
      ...props,
    }}
  />
);

describe("ChangeApprovalOperations", () => {
  it("renders as expected", async () => {
    render(<Subject />);
    await screen.findByTestId("action-button");
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
    const approveButton = await screen.findByTestId("approve-request");
    fireEvent.click(approveButton);
    await waitFor(() => {
      expect(approveChange).toHaveBeenCalled();
    });
    const openRemoteSettingsButton = await screen.findByTestId(
      "open-remote-settings",
    );
    fireEvent.click(openRemoteSettingsButton);
    expect(openRemoteSettingsButton).toHaveProperty("href", REVIEW_URL);
  });

  it("when user cannot review, an approval pending notice is displayed", async () => {
    render(
      <Subject
        {...{
          ...reviewRequestedBaseProps,
          canReview: false,
        }}
      />,
    );
    await screen.findByTestId("approval-pending");
    expect(screen.queryByTestId("approve-request")).not.toBeInTheDocument();
    expect(screen.queryByTestId("reject-request")).not.toBeInTheDocument();
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

  it("reports a rejection reason when review is rejected", async () => {
    const actionDescription = "gizmofy";
    const {
      changedBy: rejectionUser,
      message: rejectionMessage,
    } = reviewRejectedBaseProps.rejectionEvent!;
    render(
      <Subject
        {...{
          ...reviewRejectedBaseProps,
          actionDescription,
        }}
      />,
    );
    await screen.findByTestId("action-button");
    await screen.findByText(
      `The request to ${actionDescription} this experiment was`,
      { exact: false },
    );
    await screen.findByText(rejectionMessage!, { exact: false });
    await screen.findByText(rejectionUser!.email, { exact: false });
  });

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
