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

export function useChangeOperationMutation(
  experiment: Experiment | undefined,
  refetch?: () => Promise<unknown>,
  ...dataSets: Partial<ExperimentInput>[]
) {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isLoadingRefetch, setIsLoadingRefetch] = useState(false);

  const [updateExperiment, { loading: isLoadingMutation }] = useMutation<
    { updateExperiment: UpdateExperiment },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  const isLoading = isLoadingMutation || isLoadingRefetch;

  const callbacks = useMemo(
    () =>
      dataSets.map(
        (baseDataChanges: Partial<ExperimentInput>) =>
          async (
            _inputEvent?: any,
            submitDataChanges?: Partial<ExperimentInput>,
          ) => {
            try {
              setSubmitError(null);

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
                return void setSubmitError(message.status.join(", "));
              }

              if (refetch) {
                setIsLoadingRefetch(true);
                await refetch();
                setIsLoadingRefetch(false);
              }
            } catch (error) {
              setSubmitError(SUBMIT_ERROR);
            }
          },
      ),
    [updateExperiment, experiment, refetch, dataSets],
  );

  return { callbacks, isLoading, submitError };
}
