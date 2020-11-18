/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useQuery } from "@apollo/client";
import { GET_EXPERIMENT_QUERY } from "../gql/experiments";
import { getExperiment } from "../types/getExperiment";

const fieldPageMap: { [page: string]: string[] } = {
  overview: ["public_description"],
  branches: ["reference_branch"],
  audience: [
    "channels",
    "firefox_min_version",
    "targeting_config_slug",
    "proposed_enrollment",
    "proposed_duration",
  ],
};

/**
 * Hook to retrieve all Experiment data by slug.
 *
 * Result will be a loading state, a not found state, and the experiment typed
 * as getExperiment['experimentBySlug']. Refer to generated type defs under
 * ../types/getExperiment.ts
 *
 * Example:
 *
 * const { experiment, notFound, loading } = useExperiment('the-slug');
 *
 * if (loading) {
 *   return <Loading />;
 * }
 *
 * if (notFound) {
 *   return <NotFound />;
 * }
 *
 * return <h1>{experiment.name}</h1>;
 */

export function useExperiment(slug: string) {
  const { data, loading, startPolling, stopPolling } = useQuery<{
    experimentBySlug: getExperiment["experimentBySlug"];
  }>(GET_EXPERIMENT_QUERY, {
    variables: { slug },
    fetchPolicy: "network-only",
  });

  const experiment = data?.experimentBySlug;
  const missingFields = Object.keys(experiment?.readyForReview?.message || {});
  const invalidPages = Object.keys(fieldPageMap).filter((page) =>
    fieldPageMap[page].some((field) => missingFields.includes(field)),
  );
  const isMissingField = (fieldName: string) =>
    missingFields.includes(fieldName);

  return {
    experiment: experiment!,
    notFound: !loading && experiment === null,
    loading,
    startPolling,
    stopPolling,
    review: {
      ready: experiment?.readyForReview?.ready || false,
      invalidPages,
      missingFields,
      isMissingField,
    },
  };
}
