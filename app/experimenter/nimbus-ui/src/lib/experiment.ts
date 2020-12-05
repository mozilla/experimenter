/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getExperiment_experimentBySlug } from "../types/getExperiment";
import { getAllExperiments_experiments } from "../types/getAllExperiments";
import { NimbusExperimentStatus } from "../types/globalTypes";

export type StatusCheck = {
  draft: boolean;
  review: boolean;
  accepted: boolean;
  live: boolean;
  complete: boolean;
  locked: boolean;
  released: boolean;
};

export function getStatus(
  experiment?: getExperiment_experimentBySlug | getAllExperiments_experiments,
): StatusCheck {
  const status = experiment?.status;

  const released = status
    ? [NimbusExperimentStatus.LIVE, NimbusExperimentStatus.COMPLETE].includes(
        status,
      )
    : false;

  return {
    draft: status === NimbusExperimentStatus.DRAFT,
    review: status === NimbusExperimentStatus.REVIEW,
    accepted: status === NimbusExperimentStatus.ACCEPTED,
    live: status === NimbusExperimentStatus.LIVE,
    complete: status === NimbusExperimentStatus.COMPLETE,
    // The experiment's fields generally cannot be updated (accepted, live, or complete)
    locked: released || status === NimbusExperimentStatus.ACCEPTED,
    // The experiment is or was out in the wild (live or complete)
    released,
  };
}
