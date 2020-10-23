/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useQuery } from "@apollo/client";
import { GET_EXPERIMENT_QUERY } from "../gql/experiments";
import { getExperiment } from "../types/getExperiment";

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
  const { data } = useQuery<{
    experimentBySlug: getExperiment["experimentBySlug"];
  }>(GET_EXPERIMENT_QUERY, {
    variables: { slug },
    fetchPolicy: "network-only",
  });

  const experiment = data?.experimentBySlug;

  return {
    experiment,
    notFound: experiment === null,
    loading: experiment === undefined,
  };
}
