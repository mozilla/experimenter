/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { getExperiment_experimentBySlug } from "../types/getExperiment";

export type ReviewCheck = ReturnType<typeof useReviewCheck>;

const fieldPageMap: { [page: string]: string[] } = {
  overview: [
    "public_description",
    "risk_brand",
    "risk_revenue",
    "risk_partner_related",
  ],
  branches: ["reference_branch", "treatment_branches", "feature_config"],
  audience: [
    "channel",
    "firefox_min_version",
    "targeting_config_slug",
    "proposed_enrollment",
    "proposed_duration",
    "population_percent",
    "total_enrolled_clients",
  ],
};

export function useReviewCheck(
  experiment: getExperiment_experimentBySlug | null | undefined,
) {
  const missingFields = Object.keys(experiment?.readyForReview?.message || {});
  const invalidPages = Object.keys(fieldPageMap).filter((page) =>
    fieldPageMap[page].some((field) => missingFields.includes(field)),
  );
  const isMissingField = (fieldName: string) =>
    missingFields.includes(fieldName) &&
    window.location.search.includes("show-errors");

  return {
    ready: experiment?.readyForReview?.ready || false,
    invalidPages,
    missingFields,
    isMissingField,
  };
}
