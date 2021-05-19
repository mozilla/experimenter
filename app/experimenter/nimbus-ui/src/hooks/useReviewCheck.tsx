/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { Link } from "@reach/router";
import React from "react";
import { editPages } from "../components/AppLayoutWithSidebar";
import { snakeToCamelCase } from "../lib/caseConversions";
import { BASE_PATH } from "../lib/constants";
import { getExperiment_experimentBySlug } from "../types/getExperiment";

export type ReviewCheck = ReturnType<typeof useReviewCheck>;

const fieldPageMap: { [page: string]: string[] } = {
  overview: [
    "publicDescription",
    "riskBrand",
    "riskRevenue",
    "riskPartnerRelated",
  ],
  branches: ["referenceBranch", "treatmentBranches", "featureConfig"],
  audience: [
    "channel",
    "firefoxMinVersion",
    "targetingConfigSlug",
    "proposedEnrollment",
    "proposedDuration",
    "populationPercent",
    "totalEnrolledClients",
  ],
};

export function useReviewCheck(
  experiment: getExperiment_experimentBySlug | null | undefined,
) {
  let messages = (experiment?.readyForReview?.message ||
    {}) as SerializerMessages;
  messages = Object.keys(messages).reduce<SerializerMessages>((acc, cur) => {
    acc[snakeToCamelCase(cur)] = messages[cur];
    return acc;
  }, {});

  const fieldMessages = window.location.search.includes("show-errors")
    ? messages
    : {};
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
    InvalidPagesList,
  };
}
