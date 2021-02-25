/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RedirectCheck } from "../components/AppLayoutWithExperiment";
import { getAllExperiments_experiments } from "../types/getAllExperiments";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import { NimbusExperimentStatus } from "../types/globalTypes";

export function getStatus(
  experiment?: getExperiment_experimentBySlug | getAllExperiments_experiments,
) {
  const status = experiment?.status;

  // The experiment is in review or accepted state
  const preparation = [
    NimbusExperimentStatus.REVIEW,
    NimbusExperimentStatus.ACCEPTED,
  ].includes(status!);

  // The experiment is or was out in the wild (live or complete)
  const released = [
    NimbusExperimentStatus.LIVE,
    NimbusExperimentStatus.COMPLETE,
  ].includes(status!);

  // The experiment's fields generally cannot be updated (accepted, live, or complete)
  const locked = released || NimbusExperimentStatus.ACCEPTED === status!;

  return {
    draft: status === NimbusExperimentStatus.DRAFT,
    preview: status === NimbusExperimentStatus.PREVIEW,
    review: status === NimbusExperimentStatus.REVIEW,
    accepted: status === NimbusExperimentStatus.ACCEPTED,
    live: status === NimbusExperimentStatus.LIVE,
    complete: status === NimbusExperimentStatus.COMPLETE,
    locked,
    preparation,
    released,
  };
}

export type StatusCheck = ReturnType<typeof getStatus>;

// Common redirects used on all Edit page components
export function editCommonRedirects({ status }: RedirectCheck) {
  // If experiment is in review or preview, it can't be edit,
  // but it's also not locked, so send you to the review page
  if (status.review || status.preview) {
    return "request-review";
  }

  // If experiment is locked (like in review, complete),
  // send you to the summary page (slug root)
  if (status.locked) {
    return "";
  }
}
