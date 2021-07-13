/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import PageSummary from ".";
import { SERVER_ERRORS } from "../../lib/constants";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import {
  endPendingBaseProps,
  endRejectedBaseProps,
  endReviewRequestedBaseProps,
  endTimedoutBaseProps,
  enrollmentPausePendingBaseProps,
  enrollmentPauseRejectedBaseProps,
  enrollmentPauseReviewRequestedBaseProps,
  enrollmentPauseTimedoutBaseProps,
  mock,
  reviewPendingBaseProps,
  reviewRejectedBaseProps,
  reviewRequestedBaseProps,
  reviewTimedoutBaseProps,
  Subject,
} from "./mocks";

const storyWithExperimentProps = (
  props: Partial<getExperiment_experimentBySlug | null>,
  storyName?: string,
) => {
  const story = () => {
    const { mock } = mockExperimentQuery("demo-slug", props);
    return <Subject {...{ mocks: [mock] }} />;
  };
  story.storyName = storyName;
  return story;
};

export default {
  title: "pages/Summary",
  component: Subject,
  decorators: [withLinks],
};

export const missingRequiredFields = storyWithExperimentProps(
  {
    readyForReview: {
      ready: false,
      message: {
        reference_branch: [SERVER_ERRORS.NULL_FIELD],
        channel: [SERVER_ERRORS.EMPTY_LIST],
      },
    },
  },
  "Draft status, missing fields required for review",
);

export const draftStatus = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.DRAFT,
    publishStatus: NimbusExperimentPublishStatus.IDLE,
  },
  "Draft status, no missing fields",
);

export const previewStatus = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.PREVIEW,
    publishStatus: NimbusExperimentPublishStatus.IDLE,
    signoffRecommendations: {
      qaSignoff: true,
      vpSignoff: false,
      legalSignoff: false,
    },
  },
  "Preview status, one recommended signoff",
);

export const reviewRequestedCanReview = storyWithExperimentProps(
  { ...reviewRequestedBaseProps, canReview: true },
  "Launch review requested, user can review",
);

export const reviewPendingCanReview = storyWithExperimentProps(
  { ...reviewPendingBaseProps, canReview: true },
  "Launch review pending in Remote Rettings, user can review",
);

export const reviewTimedoutCanReview = storyWithExperimentProps(
  { ...reviewTimedoutBaseProps, canReview: true },
  "Launch review timed out in Remote Settings, user can review",
);

export const reviewRequestedCannotReview = storyWithExperimentProps(
  { ...reviewRequestedBaseProps, canReview: false },
  "Launch review requested, user cannot review",
);

export const reviewPendingCannotReview = storyWithExperimentProps(
  { ...reviewPendingBaseProps, canReview: false },
  "Launch review pending in Remote Rettings, user cannot review",
);

export const reviewTimedoutCannotReview = storyWithExperimentProps(
  { ...reviewTimedoutBaseProps, canReview: false },
  "Launch review timed out in Remote Settings, user cannot review",
);

export const reviewRecommendedSignoffs = storyWithExperimentProps(
  {
    ...reviewRequestedBaseProps,
    signoffRecommendations: {
      qaSignoff: true,
      vpSignoff: true,
      legalSignoff: true,
    },
  },
  "Review with all recommended sign offs",
);

export const reviewRejected = storyWithExperimentProps(
  reviewRejectedBaseProps,
  "Launch review rejected",
);

export const liveStatus = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.LIVE,
    isEnrollmentPaused: false,
  },
  "Live status",
);

export const liveUpdateRequestedCanReview = storyWithExperimentProps(
  { ...enrollmentPauseReviewRequestedBaseProps, canReview: true },
  "Enrollment end requested, user can review",
);

export const liveUpdatePendingCanReview = storyWithExperimentProps(
  { ...enrollmentPausePendingBaseProps, canReview: true },
  "Enrollment end pending in Remote Rettings, user can review",
);

export const liveUpdateTimedoutCanReview = storyWithExperimentProps(
  { ...enrollmentPauseTimedoutBaseProps, canReview: true },
  "Enrollment end timed out in Remote Settings, user can review",
);

export const liveUpdateRejected = storyWithExperimentProps(
  enrollmentPauseRejectedBaseProps,
  "Enrollment end rejected",
);

export const liveUpdateRequestedCannotReview = storyWithExperimentProps(
  { ...enrollmentPauseReviewRequestedBaseProps },
  "Enrollment end requested, user cannot review",
);

export const liveUpdatePendingCannotReview = storyWithExperimentProps(
  { ...enrollmentPausePendingBaseProps },
  "Enrollment end pending in Remote Rettings, user cannot review",
);

export const liveUpdateTimedoutCannotReview = storyWithExperimentProps(
  { ...enrollmentPauseTimedoutBaseProps },
  "Enrollment end timed out in Remote Settings, user cannot review",
);

export const endRequestedCanReview = storyWithExperimentProps(
  { ...endReviewRequestedBaseProps, canReview: true },
  "End experiment requested, user can review",
);

export const endPendingCanReview = storyWithExperimentProps(
  { ...endPendingBaseProps, canReview: true },
  "End experiment pending in Remote Rettings, user can review",
);

export const endTimedoutCanReview = storyWithExperimentProps(
  { ...endTimedoutBaseProps, canReview: true },
  "End experiment timed out in Remote Settings, user can review",
);

export const endRejected = storyWithExperimentProps(
  endRejectedBaseProps,
  "End experiment rejected",
);

export const endRequestedCannotReview = storyWithExperimentProps(
  { ...endReviewRequestedBaseProps },
  "End experiment requested, user cannot review",
);

export const endPendingCannotReview = storyWithExperimentProps(
  { ...endPendingBaseProps },
  "End experiment pending in Remote Rettings, user cannot review",
);

export const endTimedoutCannotReview = storyWithExperimentProps(
  { ...endTimedoutBaseProps },
  "End experiment timed out in Remote Settings, user cannot review",
);

export const completeStatus = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.COMPLETE,
  },
  "Complete status",
);

export const error = () => (
  <RouterSlugProvider mocks={[mock]}>
    <PageSummary polling={false} />
  </RouterSlugProvider>
);
