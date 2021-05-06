/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
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

type FieldReviewProps = {
  field: string;
  children: (props: {
    field: string;
    message: string;
  }) => React.ReactNode | null;
};

export function useReviewCheck(
  experiment: getExperiment_experimentBySlug | null | undefined,
) {
  const reviewItems = (experiment?.readyForReview?.message || {}) as Record<
    string,
    string[]
  >;
  const invalidFields = Object.keys(reviewItems);
  const invalidPages = Object.keys(fieldPageMap).filter((page) =>
    fieldPageMap[page].some((field) => invalidFields.includes(field)),
  );
  const fieldReviewMessages = (fieldName: string): string[] =>
    reviewItems[fieldName] || [];

  // EXP-981 should remove this component entirely once fieldReviewMessages is used
  // to feed these review-readiness messages directly into useCommonForm
  const FieldReview: React.FC<FieldReviewProps> = ({ field, children }) => {
    const messages = fieldReviewMessages(field);
    if (!messages.length || !window.location.search.includes("show-errors")) {
      return null;
    }

    return <>{children({ field, message: messages.join(", ") })}</>;
  };

  return {
    ready: experiment?.readyForReview?.ready || false,
    invalidPages,
    invalidFields,
    fieldReviewMessages,
    FieldReview,
  };
}
