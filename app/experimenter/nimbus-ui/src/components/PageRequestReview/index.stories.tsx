/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import PageRequestReview from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import {
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
  title: "pages/RequestReview",
  component: Subject,
  decorators: [withLinks],
};

export const missingRequiredFields = storyWithExperimentProps(
  {
    readyForReview: {
      ready: false,
      message: {
        reference_branch: ["This field may not be null."],
        channel: ["This list may not be empty."],
      },
    },
  },
  "Missing fields required for review",
);

export const draftStatus = storyWithExperimentProps({
  status: NimbusExperimentStatus.DRAFT,
  publishStatus: NimbusExperimentPublishStatus.IDLE,
});

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
  "Review requested, user can review",
);

export const reviewPendingCanReview = storyWithExperimentProps(
  { ...reviewPendingBaseProps, canReview: true },
  "Review pending in Remote Rettings, user can review",
);

export const reviewTimedoutCanReview = storyWithExperimentProps(
  { ...reviewTimedoutBaseProps, canReview: true },
  "Review timed out in Remote Settings, user can review",
);

export const reviewRequestedCannotReview = storyWithExperimentProps(
  { ...reviewRequestedBaseProps, canReview: false },
  "Review requested, user cannot review",
);

export const reviewPendingCannotReview = storyWithExperimentProps(
  { ...reviewPendingBaseProps, canReview: false },
  "Review pending in Remote Rettings, user cannot review",
);

export const reviewTimedoutCannotReview = storyWithExperimentProps(
  { ...reviewTimedoutBaseProps, canReview: false },
  "Review timed out in Remote Settings, user cannot review",
);

export const reviewRejected = storyWithExperimentProps(
  reviewRejectedBaseProps,
  "Review rejected",
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
  "Review with recommended sign offs",
);

export const error = () => (
  <RouterSlugProvider mocks={[mock]}>
    <PageRequestReview polling={false} />
  </RouterSlugProvider>
);
