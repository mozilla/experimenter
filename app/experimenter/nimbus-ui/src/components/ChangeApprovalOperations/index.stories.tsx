/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import { withLinks } from "@storybook/addon-links";
import React from "react";
import { mockChangelog } from "../../lib/mocks";
import FormApproveOrReject from "./FormApproveOrReject";
import FormRejectReason from "./FormRejectReason";
import FormRemoteSettingsPending from "./FormRemoteSettingsPending";
import {
  BaseSubject,
  reviewPendingInRemoteSettingsBaseProps,
  reviewRejectedBaseProps,
  reviewRequestedBaseProps,
  reviewTimedOutBaseProps,
  REVIEW_URL,
} from "./mocks";

const Subject = ({
  rejectChange = action("rejectChange"),
  approveChange = action("approveChange"),
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

export default {
  title: "components/ChangeApprovalOperations",
  component: Subject,
  decorators: [
    withLinks,
    (story: () => React.ReactNode) => <div className="p-5">{story()}</div>,
  ],
};

const storyWithProps = (
  props?: React.ComponentProps<typeof Subject>,
  storyName?: string,
) => {
  const story = () => <Subject {...props} />;
  if (storyName) story.storyName = storyName;
  return story;
};

export const ReviewNotRequested = storyWithProps({}, "Review not requested");

export const ReviewRequestedUserCanReview = storyWithProps(
  {
    ...reviewRequestedBaseProps,
    canReview: true,
  },
  "Review requested, user can review",
);

export const ReviewPendingInRemoteSettingsUserCanReview = storyWithProps(
  {
    ...reviewPendingInRemoteSettingsBaseProps,
    canReview: true,
  },
  "Review pending in Remote Settings, user can review",
);

export const ReviewTimedOutInRemoteSettingsUserCanReview = storyWithProps(
  {
    ...reviewTimedOutBaseProps,
    canReview: true,
  },
  "Review timed out in Remote Settings, user can review",
);

export const ReviewRejectedInExperimenterOrRemoteSettings = storyWithProps(
  {
    ...reviewRejectedBaseProps,
    canReview: true,
  },
  "Review rejected",
);

export const ReviewRequestedUserCannotReview = storyWithProps(
  {
    ...reviewRequestedBaseProps,
    canReview: false,
  },
  "Review requested, user cannot review",
);

export const ReviewPendingInRemoteSettingsUserCannotReview = storyWithProps(
  {
    ...reviewPendingInRemoteSettingsBaseProps,
    canReview: false,
  },
  "Review pending in Remote Settings, user cannot review",
);

export const ReviewTimedOutInRemoteSettingsUserCannotReview = storyWithProps(
  {
    ...reviewTimedOutBaseProps,
    canReview: false,
  },
  "Review timed out in Remote Settings, user cannot review",
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
      reviewUrl: REVIEW_URL,
      actionDescription: "frobulate",
    }}
  />
);
