/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import AppLayoutWithSidebar from ".";
import { SERVER_ERRORS } from "../../lib/constants";
import { mockChangelog } from "../../lib/mocks";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import { Subject } from "./mocks";

export default {
  title: "components/AppLayoutWithSidebar",
  component: AppLayoutWithSidebar,
  decorators: [withLinks],
};

const storyWithExperimentProps = (
  props: Partial<getExperiment_experimentBySlug>,
  storyName?: string,
) => {
  const story = () => <Subject experiment={props} />;
  story.storyName = storyName;
  return story;
};

export const MissingDetails = storyWithExperimentProps(
  {
    readyForReview: {
      ready: false,
      message: {
        reference_branch: [SERVER_ERRORS.NULL_FIELD],
        channel: [SERVER_ERRORS.EMPTY_LIST],
      },
    },
  },
  "Draft status, missing details",
);

export const DraftStatus = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.DRAFT,
  },
  "Draft status, filled out",
);

export const PreviewStatus = storyWithExperimentProps({
  status: NimbusExperimentStatus.PREVIEW,
});

export const ReviewRequestedCannotReview = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.DRAFT,
    statusNext: NimbusExperimentStatus.LIVE,
    publishStatus: NimbusExperimentPublishStatus.REVIEW,
    reviewRequest: mockChangelog(),
    canArchive: false,
  },
  "Request requiring approval was made, user cannot review",
);

export const ReviewRequestedCanReview = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.DRAFT,
    statusNext: NimbusExperimentStatus.LIVE,
    publishStatus: NimbusExperimentPublishStatus.REVIEW,
    reviewRequest: mockChangelog(),
    canReview: true,
    canArchive: false,
  },
  "Request requiring approval was made, user can review",
);

export const LiveStatus = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.LIVE,
    canArchive: false,
  },
  "Live status",
);
