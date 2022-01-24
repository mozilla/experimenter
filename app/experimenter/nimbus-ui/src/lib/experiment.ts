/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RedirectCheck } from "../lib/contexts";
import { getAllExperiments_experiments } from "../types/getAllExperiments";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "../types/globalTypes";
import { LIFECYCLE_REVIEW_FLOWS } from "./constants";

export function getStatus(
  experiment?: getExperiment_experimentBySlug | getAllExperiments_experiments,
) {
  const {
    status,
    statusNext,
    publishStatus,
    isEnrollmentPausePending,
    isArchived,
  } = experiment || {};

  // The experiment is or was out in the wild (live or complete)
  const launched = [
    NimbusExperimentStatusEnum.LIVE,
    NimbusExperimentStatusEnum.COMPLETE,
  ].includes(status!);

  return {
    archived: isArchived,
    draft: status === NimbusExperimentStatusEnum.DRAFT,
    preview: status === NimbusExperimentStatusEnum.PREVIEW,
    live: status === NimbusExperimentStatusEnum.LIVE,
    complete: status === NimbusExperimentStatusEnum.COMPLETE,
    idle: publishStatus === NimbusExperimentPublishStatusEnum.IDLE,
    approved: publishStatus === NimbusExperimentPublishStatusEnum.APPROVED,
    review: publishStatus === NimbusExperimentPublishStatusEnum.REVIEW,
    waiting: publishStatus === NimbusExperimentPublishStatusEnum.WAITING,
    // TODO: EXP-1325 Need to check something else here for end enrollment in particular?
    pauseRequested:
      status === NimbusExperimentStatusEnum.LIVE &&
      statusNext === NimbusExperimentStatusEnum.LIVE &&
      isEnrollmentPausePending === true,
    endRequested:
      status === NimbusExperimentStatusEnum.LIVE &&
      statusNext === NimbusExperimentStatusEnum.COMPLETE,
    launched,
  };
}

export type StatusCheck = ReturnType<typeof getStatus>;

// Common redirects used on all Edit page components
//export function editCommonRedirects({ status }: RedirectCheck) {
export function editCommonRedirects(check: RedirectCheck) {
  const { status } = check;
  // If experiment is launched or the user can't edit the experiment,
  // send them to the summary page
  if (status.launched || !status.idle || status.preview || status.archived) {
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

  if (!status.launched && !status.archived) {
    return "Request Launch";
  }
  return "";
}

export type ExperimentSortSelector =
  | keyof getAllExperiments_experiments
  | ((experiment: getAllExperiments_experiments) => string | undefined);

export const featureConfigNameSortSelector: ExperimentSortSelector = (
  experiment,
) => experiment.featureConfig?.name;

export const ownerUsernameSortSelector: ExperimentSortSelector = (experiment) =>
  experiment.owner?.username;

export const enrollmentSortSelector: ExperimentSortSelector = ({
  startDate,
  proposedEnrollment,
}) => {
  if (startDate) {
    const startTime = new Date(startDate).getTime();
    const enrollmentMS = proposedEnrollment * (1000 * 60 * 60 * 24);
    return new Date(startTime + enrollmentMS).toISOString();
  } else {
    return "" + proposedEnrollment;
  }
};

export const resultsReadySortSelector: ExperimentSortSelector = (experiment) =>
  experiment.resultsReady ? "1" : "0";

export const selectFromExperiment = (
  experiment: getAllExperiments_experiments,
  selectBy: ExperimentSortSelector,
) =>
  "" +
  (typeof selectBy === "function"
    ? selectBy(experiment)
    : experiment[selectBy]);

export const experimentSortComparator =
  (sortBy: ExperimentSortSelector, descending: boolean) =>
  (
    experimentA: getAllExperiments_experiments,
    experimentB: getAllExperiments_experiments,
  ) => {
    const orderBy = descending ? -1 : 1;
    const propertyA = selectFromExperiment(experimentA, sortBy);
    const propertyB = selectFromExperiment(experimentB, sortBy);
    return orderBy * propertyA.localeCompare(propertyB);
  };
