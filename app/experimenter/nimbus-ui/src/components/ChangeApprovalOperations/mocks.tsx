/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Button from "react-bootstrap/Button";
import ChangeApprovalOperations from ".";
import { mockChangelog } from "../../lib/mocks";
import { NimbusExperimentPublishStatus } from "../../types/globalTypes";

type BaseSubjectProps = Partial<
  React.ComponentProps<typeof ChangeApprovalOperations>
>;

export const REVIEW_URL =
  "http://localhost:8888/v1/admin/#/buckets/main-workspace/collections/nimbus-mobile-experiments/records";

export const BaseSubject = ({
  actionDescription = "frobulate",
  isLoading = false,
  canReview = false,
  publishStatus = NimbusExperimentPublishStatus.IDLE,
  reviewRequestEvent,
  rejectionEvent,
  timeoutEvent,
  rejectChange = () => {},
  approveChange = () => {},
  ...props
}: BaseSubjectProps) => (
  <ChangeApprovalOperations
    {...{
      actionDescription,
      isLoading,
      canReview,
      publishStatus,
      reviewRequestEvent,
      rejectionEvent,
      timeoutEvent,
      rejectChange,
      approveChange,
      reviewUrl: REVIEW_URL,
      ...props,
    }}
  >
    <Button data-testid="action-button" className="mr-2 btn btn-success">
      Frobulate experiment
    </Button>
  </ChangeApprovalOperations>
);

export const reviewRequestedBaseProps: BaseSubjectProps = {
  publishStatus: NimbusExperimentPublishStatus.REVIEW,
  reviewRequestEvent: mockChangelog(
    "abc@def.com",
    null,
    "2020-04-13T01:00:00Z",
  ),
};

export const reviewApprovedBaseProps: BaseSubjectProps = {
  publishStatus: NimbusExperimentPublishStatus.APPROVED,
  reviewRequestEvent: mockChangelog(
    "abc@def.com",
    null,
    "2020-04-13T01:00:00Z",
  ),
};

export const reviewPendingInRemoteSettingsBaseProps: BaseSubjectProps = {
  publishStatus: NimbusExperimentPublishStatus.WAITING,
  reviewRequestEvent: mockChangelog(
    "abc@def.com",
    null,
    "2020-04-13T01:00:00Z",
  ),
};

export const reviewTimedOutBaseProps: BaseSubjectProps = {
  publishStatus: NimbusExperimentPublishStatus.REVIEW,
  reviewRequestEvent: mockChangelog(
    "abc@def.com",
    null,
    "2020-04-13T01:00:00Z",
  ),
  timeoutEvent: mockChangelog("def@mozilla.com", null, "2020-04-13T03:00:00Z"),
};

export const reviewRejectedBaseProps: BaseSubjectProps = {
  publishStatus: NimbusExperimentPublishStatus.IDLE,
  reviewRequestEvent: mockChangelog(
    "abc@def.com",
    null,
    "2020-04-13T01:00:00Z",
  ),
  rejectionEvent: mockChangelog(
    "ghi@mozilla.com",
    "It's bad. Just start over.",
    "2020-04-13T02:00:00Z",
  ),
};

export const reviewRequestedAfterRejectionBaseProps: BaseSubjectProps = {
  ...reviewRejectedBaseProps,
  publishStatus: NimbusExperimentPublishStatus.REVIEW,
  reviewRequestEvent: mockChangelog(
    "abc@def.com",
    null,
    "2020-04-13T10:00:00Z",
  ),
};

export const reviewApprovedAfterTimeoutBaseProps: BaseSubjectProps = {
  ...reviewTimedOutBaseProps,
  publishStatus: NimbusExperimentPublishStatus.APPROVED,
};
