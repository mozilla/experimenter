/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { reviewRequestedBaseProps, Subject } from "./mocks";

const storyWithExperimentProps = (
  props?: Partial<getExperiment_experimentBySlug | null>,
  storyName?: string,
) => {
  const story = () => {
    return <Subject {...{ props }} />;
  };
  story.storyName = storyName;
  return story;
};

export default {
  title: "components/Summary",
  component: Subject,
  decorators: [withLinks],
};

export const draftStatus = storyWithExperimentProps();

export const liveStatus = storyWithExperimentProps({
  status: NimbusExperimentStatus.LIVE,
});

export const enrollmentActive = storyWithExperimentProps({
  status: NimbusExperimentStatus.LIVE,
  isEnrollmentPaused: false,
});

export const enrollmentEnded = storyWithExperimentProps({
  status: NimbusExperimentStatus.LIVE,
  enrollmentEndDate: new Date().toISOString(),
});

export const endRequestedEnrollmentEnded = storyWithExperimentProps({
  ...reviewRequestedBaseProps,
  enrollmentEndDate: new Date().toISOString(),
});

export const noBranches = storyWithExperimentProps({
  referenceBranch: null,
  treatmentBranches: null,
});
