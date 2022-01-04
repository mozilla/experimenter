/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import SummaryTimeline from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "../../../types/globalTypes";

export const Subject = ({
  startDate = "2020-11-28T14:52:44.704811+00:00",
  computedEndDate = "2020-12-08T14:52:44.704811+00:00",
  computedDurationDays = 10,
  computedEnrollmentDays = 1,
  status = NimbusExperimentStatusEnum.DRAFT,
  publishStatus = NimbusExperimentPublishStatusEnum.IDLE,
}: {
  startDate?: string;
  computedEndDate?: string;
  computedDurationDays?: number;
  computedEnrollmentDays?: number;
  status?: NimbusExperimentStatusEnum;
  publishStatus?: NimbusExperimentPublishStatusEnum;
}) => {
  const { experiment } = mockExperimentQuery("something-vague", {
    startDate,
    computedEndDate,
    computedDurationDays,
    computedEnrollmentDays,
    status,
    publishStatus,
  });
  return <SummaryTimeline {...{ experiment }} />;
};
