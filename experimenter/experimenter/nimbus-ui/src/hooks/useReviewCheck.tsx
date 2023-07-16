/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link } from "@reach/router";
import React from "react";
import { editPages } from "src/components/AppLayoutWithSidebar";
import { BASE_PATH } from "src/lib/constants";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

export type ReviewCheck = ReturnType<typeof useReviewCheck>;

const fieldPageMap: { [page: string]: string[] } = {
  overview: [
    "public_description",
    "risk_brand",
    "risk_revenue",
    "risk_partner_related",
  ],
  branches: [
    "reference_branch",
    "treatment_branches",
    "feature_configs",
    "is_rollout",
    "localizations",
  ],
  audience: [
    "channel",
    "firefox_min_version",
    "languages",
    "locales",
    "countries",
    "targeting_config_slug",
    "proposed_enrollment",
    "proposed_duration",
    "population_percent",
    "total_enrolled_clients",
    "required_experiments",
    "excluded_experiments",
  ],
};

export function useReviewCheck(
  experiment: getExperiment_experimentBySlug | null | undefined,
) {
  const messages = (experiment?.readyForReview?.message ||
    {}) as SerializerMessages;
  const fieldMessages = window.location.search.includes("show-errors")
    ? messages
    : {};
  const fieldWarnings = (experiment?.readyForReview?.warnings ||
    {}) as SerializerMessages;
  const invalidPages = Object.keys(fieldPageMap).filter((page) =>
    fieldPageMap[page].some((field) => Object.keys(messages).includes(field)),
  );

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
    fieldMessages,
    fieldWarnings,
    InvalidPagesList,
  };
}
