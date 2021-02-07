/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getAllExperiments_experiments } from "../types/getAllExperiments";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import { NimbusExperimentStatus } from "../types/globalTypes";

export type ReviewReadiness = {
  ready: boolean;
  invalidPages: string[];
  missingFields: string[];
  isMissingField: (fieldName: string) => boolean;
};

export function getStatus(
  experiment?:
    | getExperiment_experimentBySlug
    | getAllExperiments_experiments
    | null,
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

const fieldPageMap: { [page: string]: string[] } = {
  overview: ["public_description", "risk_mitigation_link"],
  branches: ["reference_branch", "treatment_branches"],
  audience: [
    "channel",
    "firefox_min_version",
    "targeting_config_slug",
    "proposed_enrollment",
    "proposed_duration",
    "population_percent",
  ],
};

export function getReviewReadiness(
  experiment?: getExperiment_experimentBySlug | null | undefined,
): ReviewReadiness {
  const ready = experiment?.readyForReview?.ready || false;
  const missingFields = Object.keys(experiment?.readyForReview?.message || {});
  const invalidPages = Object.keys(fieldPageMap).filter((page) =>
    fieldPageMap[page].some((field) => missingFields.includes(field)),
  );

  const isMissingField = (fieldName: string) =>
    missingFields.includes(fieldName) &&
    // This is a bit hacky, but we only want to visually display missing field
    // errors when you click the links under the "Missing details" section, not
    // from a regular sidebar navigation link
    window.location.search.includes("show-errors");

  return {
    ready,
    invalidPages,
    missingFields,
    isMissingField,
  };
}
