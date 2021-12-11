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

const CHANGE_MUTATION_DISPLAY_ERROR_FIELDS = ["status", "status_next"];

export function useChangeOperationMutation(
  experiment: Experiment | undefined,
  refetch?: () => Promise<unknown>,
  ...dataSets: Partial<ExperimentInput>[]
) {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const [updateExperiment] = useMutation<
    { updateExperiment: UpdateExperiment },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  const callbacks = useMemo(
    () =>
      dataSets.map(
        (baseDataChanges: Partial<ExperimentInput>) =>
          async (
            _inputEvent?: any,
            submitDataChanges?: Partial<ExperimentInput>,
          ) => {
            setIsLoading(true);
            setSubmitError(null);

            try {
              const result = await updateExperiment({
                variables: {
                  input: {
                    id: experiment?.id,
                    ...baseDataChanges,
                    ...submitDataChanges,
                  },
                },
              });

              // istanbul ignore next - can't figure out how to trigger this in a test
              if (!result.data?.updateExperiment) {
                throw new Error(SUBMIT_ERROR);
              }

              const { message } = result.data.updateExperiment;

              if (
                message &&
                message !== "success" &&
                typeof message === "object"
              ) {
                const errors = [];
                for (const name of CHANGE_MUTATION_DISPLAY_ERROR_FIELDS) {
                  if (message[name]) {
                    errors.push(...message[name]);
                  }
                }
                setSubmitError(
                  errors.length ? errors.join(", ") : SUBMIT_ERROR,
                );
              }
              if (refetch) {
                await refetch();
              }
            } catch (error) {
              setSubmitError(SUBMIT_ERROR);
            }
            setIsLoading(false);
          },
      ),
    [
      updateExperiment,
      experiment,
      refetch,
      dataSets,
      setIsLoading,
      setSubmitError,
    ],
  );

  return { callbacks, isLoading, submitError };
}
