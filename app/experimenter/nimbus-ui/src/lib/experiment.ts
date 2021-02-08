/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getAllExperiments_experiments } from "../types/getAllExperiments";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import { NimbusExperimentStatus } from "../types/globalTypes";

export function getStatus(
  experiment?: getExperiment_experimentBySlug | getAllExperiments_experiments,
) {
  const status = experiment?.status;

  const released = status
    ? [NimbusExperimentStatus.LIVE, NimbusExperimentStatus.COMPLETE].includes(
        status,
      )
    : false;

  return {
    draft: status === NimbusExperimentStatus.DRAFT,
    // @ts-ignore EXP-866 mock value until backend API & types are updated
    preview: status === "PREVIEW",
    review: status === NimbusExperimentStatus.REVIEW,
    accepted: status === NimbusExperimentStatus.ACCEPTED,
    live: status === NimbusExperimentStatus.LIVE,
    complete: status === NimbusExperimentStatus.COMPLETE,
    // The experiment's fields generally cannot be updated (accepted, live, or complete)
    locked: released || status === NimbusExperimentStatus.ACCEPTED,
    // The experiment is in review, preview, or accepted state
    preparation: [
      NimbusExperimentStatus.REVIEW,
      "PREVIEW", // EXP-866 mock value until backend API & types are updated
      NimbusExperimentStatus.ACCEPTED,
    ].includes(status!),
    // The experiment is or was out in the wild (live or complete)
    released,
  };
}

export type StatusCheck = ReturnType<typeof getStatus>;

export function editCommonRedirects({ status }: { status: StatusCheck }) {
  if (status.review) {
    return "request-review";
  }

  if (status.locked) {
    return "design";
  }
}
