/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import { mockExperimentQuery } from "../../lib/mocks";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import { Subject } from "./mocks";

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
  title: "pages/SummaryDetails",
  component: Subject,
  decorators: [withLinks],
};

export const draftStatus = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.DRAFT,
    publishStatus: NimbusExperimentPublishStatus.IDLE,
  },
  "Draft status, no missing fields",
);

export const draftArchived = storyWithExperimentProps(
  {
    isArchived: true,
    canEdit: false,
  },
  "Draft status, archived",
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

export const liveStatus = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.LIVE,
    isEnrollmentPaused: false,
  },
  "Live status",
);

export const liveStatusPaused = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.LIVE,
    isEnrollmentPaused: true,
    enrollmentEndDate: new Date().toISOString(),
  },
  "Live status, enrollment paused",
);

export const completeStatus = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.COMPLETE,
  },
  "Complete status",
);

export const completeArchived = storyWithExperimentProps(
  {
    status: NimbusExperimentStatus.COMPLETE,
    isArchived: true,
    canEdit: false,
  },
  "Complete status, archived",
);
