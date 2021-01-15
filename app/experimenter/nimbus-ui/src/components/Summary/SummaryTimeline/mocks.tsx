/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import SummaryTimeline from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { NimbusExperimentStatus } from "../../../types/globalTypes";

export const Subject = ({
  startDate = "2020-11-28T14:52:44.704811+00:00",
  endDate = "2020-12-08T14:52:44.704811+00:00",
  proposedDuration = 10,
  proposedEnrollment = 1,
  status = NimbusExperimentStatus.DRAFT,
}: {
  startDate?: string;
  endDate?: string;
  proposedDuration?: number;
  proposedEnrollment?: number;
  status?: NimbusExperimentStatus;
}) => {
  const { experiment } = mockExperimentQuery("something-vague", {
    startDate,
    endDate,
    proposedDuration,
    proposedEnrollment,
    status,
  });
  return <SummaryTimeline {...{ experiment }} />;
};
