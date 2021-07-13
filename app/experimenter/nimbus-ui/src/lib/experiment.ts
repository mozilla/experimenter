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
import { LIFECYCLE_REVIEW_FLOWS } from "./constants";

export function getStatus(
  experiment?: getExperiment_experimentBySlug | getAllExperiments_experiments,
) {
  const { status, statusNext, publishStatus, isEnrollmentPausePending } =
    experiment || {};

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
    // TODO: EXP-1325 Need to check something else here for end enrollment in particular?
    pauseRequested:
      status === NimbusExperimentStatus.LIVE &&
      statusNext === NimbusExperimentStatus.LIVE &&
      isEnrollmentPausePending === true,
    endRequested:
      status === NimbusExperimentStatus.LIVE &&
      statusNext === NimbusExperimentStatus.COMPLETE,
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

export function getSummaryAction(
  status: StatusCheck,
  canReview: boolean | null,
) {
  // has pending review approval
  if (status.review || status.approved || status.waiting) {
    const stringName = !canReview ? "requestSummary" : "reviewSummary";
    if (status.pauseRequested) {
      return LIFECYCLE_REVIEW_FLOWS.PAUSE[stringName];
    }
    if (status.endRequested) {
      return LIFECYCLE_REVIEW_FLOWS.END[stringName];
    } else {
      return LIFECYCLE_REVIEW_FLOWS.LAUNCH[stringName];
    }
  }

  if (!status.launched) {
    return "Request Launch";
  }
  return "";
}
