/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { useMemo, useState } from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../gql/experiments";
import { SUBMIT_ERROR } from "../lib/constants";
import { getExperiment_experimentBySlug as Experiment } from "../types/getExperiment";
import { ExperimentInput } from "../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperiment } from "../types/updateExperiment";

export const ARCHIVING_EXPERIMENT = "Archiving experiment";
export const UNARCHIVING_EXPERIMENT = "Unarchiving experiment";

export function useArchive(
  experiment: Partial<Experiment>,
  refetch: () => Promise<unknown>,
) {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [updateExperiment] = useMutation<
    { updateExperiment: UpdateExperiment },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  const callback = useMemo(
    () => async () => {
      setIsLoading(true);
      setSubmitError(null);

      try {
        const result = await updateExperiment({
          variables: {
            input: {
              id: experiment?.id,
              isArchived: !experiment.isArchived,
              changelogMessage: !experiment.isArchived
                ? ARCHIVING_EXPERIMENT
                : UNARCHIVING_EXPERIMENT,
            },
          },
        });

        if (!result.data?.updateExperiment) {
          throw new Error(SUBMIT_ERROR);
        }

        const { message } = result.data.updateExperiment;

        if (message && message !== "success" && typeof message === "object") {
          throw new Error(JSON.stringify(message));
        }

        await refetch();
      } catch (error) {
        setSubmitError(error.message);
      }
      setIsLoading(false);
    },

    [updateExperiment, experiment, refetch],
  );

  return { callback, isLoading, submitError };
}
