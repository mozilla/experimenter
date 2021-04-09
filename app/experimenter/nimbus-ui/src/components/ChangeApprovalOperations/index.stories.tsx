/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import { withLinks } from "@storybook/addon-links";
import React from "react";
import FormApproveOrReject from "./FormApproveOrReject";
import FormRejectReason from "./FormRejectReason";
import FormRemoteSettingsPending from "./FormRemoteSettingsPending";
import { BaseSubject, mockChangelog } from "./mocks";

const Subject = ({
  rejectChange = action("rejectChange"),
  approveChange = action("approveChange"),
  startRemoteSettingsApproval = action("startRemoteSettingsApproval"),
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

export default {
  title: "components/ChangeApprovalOperations",
  component: Subject,
  decorators: [
    withLinks,
    (story: Function) => <div className="p-5">{story()}</div>,
  ],
};

export const ReviewNotRequested = () => <Subject />;

export const ReviewRequestedUserCanReview = () => (
  <Subject
    {...{
      reviewRequestEvent: mockChangelog(),
      canReview: true,
    }}
  />
);

export const ReviewPendingInRemoteSettingsUserCanReview = () => (
  <Subject
    {...{
      reviewRequestEvent: mockChangelog(),
      approvalEvent: mockChangelog("def@mozilla.com"),
      canReview: true,
    }}
  />
);

export const ReviewTimedOutInRemoteSettingsUserCanReview = () => (
  <Subject
    {...{
      reviewRequestEvent: mockChangelog(),
      approvalEvent: mockChangelog("def@mozilla.com"),
      timeoutEvent: mockChangelog("ghi@mozilla.com"),
      canReview: true,
    }}
  />
);

export const ReviewRequestedUserCannotReview = () => (
  <Subject
    {...{
      reviewRequestEvent: mockChangelog(),
      canReview: false,
    }}
  />
);

export const ReviewPendingInRemoteSettingsUserCannotReview = () => (
  <Subject
    {...{
      reviewRequestEvent: mockChangelog(),
      approvalEvent: mockChangelog("def@mozilla.com"),
      canReview: false,
    }}
  />
);

export const ReviewTimedOutInRemoteSettingsUserCannotReview = () => (
  <Subject
    {...{
      reviewRequestEvent: mockChangelog(),
      approvalEvent: mockChangelog("def@mozilla.com"),
      timeoutEvent: mockChangelog("ghi@mozilla.com"),
      canReview: false,
    }}
  />
);

export const ReviewRejectedInExperimenterOrRemoteSettings = () => (
  <Subject
    {...{
      reviewRequestEvent: mockChangelog(),
      approvalEvent: mockChangelog("def@mozilla.com"),
      rejectionEvent: mockChangelog(
        "ghi@mozilla.com",
        "It's bad. Just start over.",
      ),
      canReview: true,
    }}
  />
);

export const FormApproveOrRejectStory = () => (
  <FormApproveOrReject
    {...{
      actionDescription: "froblulate",
      isLoading: false,
      reviewRequestEvent: mockChangelog(),
      timeoutEvent: mockChangelog("ghi@mozilla.com"),
      onApprove: action("approve"),
      onReject: action("reject"),
    }}
  />
);
export const FormRejectReasonStory = () => (
  <FormRejectReason
    {...{
      isLoading: false,
      onSubmit: action("submit"),
      onCancel: action("cancel"),
    }}
  />
);

export const FormRemoteSettingsPendingStory = () => (
  <FormRemoteSettingsPending
    {...{
      isLoading: false,
      onConfirm: action("confirm"),
    }}
  />
);
