/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import SummaryTimeline from "src/components/Summary/SummaryTimeline";
import { mockExperimentQuery } from "src/lib/mocks";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "src/types/globalTypes";

export const Subject = ({
  startDate = "2020-11-28T14:52:44.704811+00:00",
  computedEnrollmentEndDate = "2020-12-02T14:52:44.704811+00:00",
  computedEndDate = "2020-12-08T14:52:44.704811+00:00",
  computedDurationDays = 10,
  computedEnrollmentDays = 1,
  proposedReleaseDate = "",
  status = NimbusExperimentStatusEnum.DRAFT,
  publishStatus = NimbusExperimentPublishStatusEnum.IDLE,
  isRollout = false,
  isFirstRun = false,
}: {
  startDate?: string;
  computedDurationDays?: number;
  computedEndDate?: string;
  computedEnrollmentDays?: number;
  computedEnrollmentEndDate?: string;
  proposedReleaseDate?: string;
  status?: NimbusExperimentStatusEnum;
  publishStatus?: NimbusExperimentPublishStatusEnum;
  isRollout?: boolean;
  isFirstRun?: boolean;
}) => {
  const { experiment } = mockExperimentQuery("something-vague", {
    startDate,
    computedDurationDays,
    computedEndDate,
    computedEnrollmentDays,
    computedEnrollmentEndDate,
    proposedReleaseDate,
    status,
    publishStatus,
    isRollout,
    isFirstRun,
  });
  return <SummaryTimeline {...{ experiment }} />;
};
