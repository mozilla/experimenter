/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Button from "react-bootstrap/Button";
import ChangeApprovalOperations from ".";
import { NimbusChangeLogType, NimbusUser } from "./temp-types";

export const mockUser = (
  email: string | null = "abc@mozilla.com",
): NimbusUser => ({
  email,
});

export const mockChangelog = (
  email: string | null = "abc@mozilla.com",
  message: string | null = null,
  changedOn: DateTime | null = new Date().toISOString(),
): NimbusChangeLogType => ({
  changedBy: mockUser(email),
  changedOn,
  message,
});

export const BaseSubject = ({
  actionDescription = "frobulate",
  isLoading = false,
  canReview = false,
  reviewRequestEvent,
  approvalEvent,
  rejectionEvent,
  timeoutEvent,
  rejectChange = () => {},
  approveChange = () => {},
  startRemoteSettingsApproval = () => {},
  ...props
}: Partial<React.ComponentProps<typeof ChangeApprovalOperations>>) => (
  <ChangeApprovalOperations
    {...{
      featureFlags: {
        exp1055ReviewFlow: true,
      },
      actionDescription,
      isLoading,
      canReview,
      reviewRequestEvent,
      approvalEvent,
      rejectionEvent,
      timeoutEvent,
      rejectChange,
      approveChange,
      startRemoteSettingsApproval,
      ...props,
    }}
  >
    <Button data-testid="action-button" className="mr-2 btn btn-success">
      Frobulate experiment
    </Button>
  </ChangeApprovalOperations>
);
