/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link } from "@reach/router";
import React from "react";
import { editPages } from "../components/AppLayoutWithSidebar";
import InlineErrorIcon from "../components/InlineErrorIcon";
import { BASE_PATH } from "../lib/constants";
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
  const reviewItems = (experiment?.readyForReview?.message || {}) as Record<
    string,
    string[]
  >;
  const invalidPages = Object.keys(fieldPageMap).filter((page) =>
    fieldPageMap[page].some((field) =>
      Object.keys(reviewItems).includes(field),
    ),
  );
  const fieldReviewMessages = (fieldName: string): string[] =>
    reviewItems[fieldName] || [];

  // EXP-981 should remove this component entirely once fieldReviewMessages is used
  // to feed these review-readiness messages directly into useCommonForm
  const FieldReview: React.FC<{
    field: string;
  }> = ({ field }) => {
    const messages = fieldReviewMessages(field);
    if (!messages.length || !window.location.search.includes("show-errors")) {
      return null;
    }

    return (
      <span className="align-text-bottom ml-1">
        <InlineErrorIcon {...{ field, message: messages.join(", ") }} />
      </span>
    );
  };
  const InvalidPagesList: React.FC = () => (
    <>
      {experiment &&
        invalidPages.map((missingPage, idx) => {
          const editPage = editPages.find((p) => p.slug === missingPage)!;

          return (
            <React.Fragment key={`missing-${idx}`}>
              <Link
                to={`${BASE_PATH}/${experiment.slug}/edit/${editPage.slug}?show-errors`}
                data-testid={`missing-detail-link-${editPage.slug}`}
              >
                {editPage.name}
              </Link>

              {idx !== invalidPages.length - 1 && ", "}
            </React.Fragment>
          );
        })}
    </>
  );

  return {
    ready: experiment?.readyForReview?.ready || false,
    invalidPages,
    fieldReviewMessages,
    FieldReview,
    InvalidPagesList,
  };
}
