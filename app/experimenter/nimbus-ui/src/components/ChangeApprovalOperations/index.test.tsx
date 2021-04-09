/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { BaseSubject, mockChangelog } from "./mocks";

const Subject = ({
  rejectChange = () => {},
  approveChange = () => {},
  startRemoteSettingsApproval = () => {},
  ...props
}: React.ComponentProps<typeof BaseSubject>) => (
  <BaseSubject
    {...{
      rejectChange,
      approveChange,
      startRemoteSettingsApproval,
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
    const startRemoteSettingsApproval = jest.fn();
    render(
      <Subject
        {...{
          canReview: true,
          reviewRequestEvent: mockChangelog(),
          approveChange,
          startRemoteSettingsApproval,
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
    expect(startRemoteSettingsApproval).toHaveBeenCalled();
  });

  it("when user cannot review, an approval pending notice is displayed", async () => {
    render(
      <Subject
        {...{
          canReview: false,
          reviewRequestEvent: mockChangelog(),
        }}
      />,
    );
    await screen.findByTestId("approval-pending");
    expect(screen.queryByTestId("approve-request")).not.toBeInTheDocument();
    expect(screen.queryByTestId("reject-request")).not.toBeInTheDocument();
  });

  it("when user can review and review has been approved, button to open remote settings is offered", async () => {
    const startRemoteSettingsApproval = jest.fn();
    render(
      <Subject
        {...{
          canReview: true,
          reviewRequestEvent: mockChangelog(),
          approvalEvent: mockChangelog(),
          startRemoteSettingsApproval,
        }}
      />,
    );
    const openRemoteSettingsButton = await screen.findByTestId(
      "open-remote-settings",
    );
    fireEvent.click(openRemoteSettingsButton);
    expect(startRemoteSettingsApproval).toHaveBeenCalled();
  });

  it("when user cannot review and review has been approved, an approval pending notice is displayed", async () => {
    const startRemoteSettingsApproval = jest.fn();
    render(
      <Subject
        {...{
          canReview: false,
          reviewRequestEvent: mockChangelog(),
          approvalEvent: mockChangelog(),
          startRemoteSettingsApproval,
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
          canReview: true,
          reviewRequestEvent: mockChangelog(),
          rejectChange,
        }}
      />,
    );
    const rejectButton = await screen.findByTestId("reject-request");
    fireEvent.click(rejectButton);
    const rejectSubmitButton = await screen.findByTestId("reject-submit");
    const rejectReasonField = await screen.findByTestId("reject-reason");
    expect(rejectSubmitButton).not.toBeEnabled();
    fireEvent.change(rejectReasonField, {
      target: { value: expectedReason },
    });
    fireEvent.blur(rejectReasonField);
    await waitFor(() => {
      expect(rejectSubmitButton).toBeEnabled();
    });
    fireEvent.click(rejectSubmitButton);
    await waitFor(() => {
      expect(rejectChange).toBeCalledWith({ reason: expectedReason });
    });
  });

  it("when user can review, supports rejection and cancelling", async () => {
    const rejectChange = jest.fn();
    render(
      <Subject
        {...{
          canReview: true,
          reviewRequestEvent: mockChangelog(),
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
    const rejectionUser = "jdoe@mozilla.com";
    const rejectionMessage = "chutes too narrow";
    render(
      <Subject
        {...{
          actionDescription,
          reviewRequestEvent: mockChangelog(),
          rejectionEvent: mockChangelog(rejectionUser, rejectionMessage),
        }}
      />,
    );
    await screen.findByTestId("action-button");
    await screen.findByText(
      `The request to ${actionDescription} this experiment was`,
      { exact: false },
    );
    await screen.findByText(rejectionMessage, { exact: false });
    await screen.findByText(rejectionUser, { exact: false });
  });

  it("when user can review and review has timed out, a timeout notice is displayed", async () => {
    render(
      <Subject
        {...{
          canReview: true,
          reviewRequestEvent: mockChangelog(),
          timeoutEvent: mockChangelog(),
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
          canReview: false,
          reviewRequestEvent: mockChangelog(),
          timeoutEvent: mockChangelog(),
        }}
      />,
    );
    await screen.findByTestId("approval-pending");
    expect(screen.queryByTestId("timeout-notice")).not.toBeInTheDocument();
    expect(screen.queryByTestId("approve-request")).not.toBeInTheDocument();
    expect(screen.queryByTestId("reject-request")).not.toBeInTheDocument();
  });
});
