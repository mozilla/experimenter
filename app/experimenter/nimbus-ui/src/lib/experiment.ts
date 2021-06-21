/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RedirectCheck } from "../components/AppLayoutWithExperiment";
import { getAllExperiments_experiments } from "../types/getAllExperiments";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../types/globalTypes";

export function getStatus(
  experiment?: getExperiment_experimentBySlug | getAllExperiments_experiments,
) {
  const status = experiment?.status;
  const publishStatus = experiment?.publishStatus;

  // The experiment is or was out in the wild (live or complete)
  const launched = [
    NimbusExperimentStatus.LIVE,
    NimbusExperimentStatus.COMPLETE,
  ].includes(status!);

  return {
    draft: status === NimbusExperimentStatus.DRAFT,
    preview: status === NimbusExperimentStatus.PREVIEW,
    live: status === NimbusExperimentStatus.LIVE,
    complete: status === NimbusExperimentStatus.COMPLETE,
    idle: publishStatus === NimbusExperimentPublishStatus.IDLE,
    approved: publishStatus === NimbusExperimentPublishStatus.APPROVED,
    review: publishStatus === NimbusExperimentPublishStatus.REVIEW,
    waiting: publishStatus === NimbusExperimentPublishStatus.WAITING,
    endRequested: experiment?.statusNext === NimbusExperimentStatus.COMPLETE,
    launched,
  };
}

export type StatusCheck = ReturnType<typeof getStatus>;

// Common redirects used on all Edit page components
export function editCommonRedirects({ status }: RedirectCheck) {
  // If experiment is launched or the user can't edit the experiment,
  // send them to the summary page
  if (status.launched || !status.idle || status.preview) {
    return "";
  }
}
