/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { useCallback, useState } from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
import {
  CHANGELOG_MESSAGES,
  SAVE_FAILED_NO_ERROR,
  SUBMIT_ERROR,
} from "src/lib/constants";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import {
  updateExperiment,
  updateExperimentVariables,
} from "src/types/updateExperiment";

// Params are a select subset of experiment properties
export type UseTakeawaysExperimentSubset = Pick<
  getExperiment_experimentBySlug,
  | "id"
  | "conclusionRecommendation"
  | "conclusionRecommendations"
  | "takeawaysSummary"
  | "takeawaysQbrLearning"
  | "takeawaysMetricGain"
  | "takeawaysGainAmount"
  | "isArchived"
>;

export type UseTakeawaysResult = UseTakeawaysExperimentSubset & {
  showEditor: boolean;
  setShowEditor: React.Dispatch<React.SetStateAction<boolean>>;
  isLoading: boolean;
  onSubmit: (data: Record<string, any>) => Promise<void>;
  isServerValid: boolean;
  submitErrors: SerializerMessages;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
};

export const useTakeaways = (
  params: UseTakeawaysExperimentSubset,
  refetch?: () => Promise<unknown>,
): UseTakeawaysResult => {
  const [isLoading, setIsLoading] = useState(false);
  const [showEditor, setShowEditor] = useState(false);
  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const [isServerValid, setIsServerValid] = useState(true);
  const [updateExperiment] = useMutation<
    updateExperiment,
    updateExperimentVariables
  >(UPDATE_EXPERIMENT_MUTATION);

  const onSubmit = useCallback(
    ({ id }: UseTakeawaysExperimentSubset, refetch?: () => Promise<unknown>) =>
      async (data: Record<string, any>) => {
        const {
          conclusionRecommendation,
          conclusionRecommendations,
          takeawaysSummary,
          takeawaysQbrLearning,
          takeawaysMetricGain,
          takeawaysGainAmount,
        } = data;

        try {
          setIsLoading(true);
          const variables = {
            input: {
              id,
              conclusionRecommendation: conclusionRecommendation || null,
              conclusionRecommendations: conclusionRecommendations || [],
              takeawaysSummary,
              takeawaysQbrLearning: takeawaysQbrLearning,
              takeawaysMetricGain: takeawaysMetricGain,
              takeawaysGainAmount: takeawaysGainAmount,
              changelogMessage: CHANGELOG_MESSAGES.UPDATED_TAKEAWAYS,
            },
          };

          const result = await updateExperiment({ variables });
          if (!result.data?.updateExperiment) {
            throw new Error(SAVE_FAILED_NO_ERROR);
          }

          const { message } = result.data.updateExperiment;

          if (message && message !== "success" && typeof message === "object") {
            setIsServerValid(false);
            setIsLoading(false);
            setSubmitErrors(message);
          } else {
            if (refetch) await refetch();
            setIsServerValid(true);
            setSubmitErrors({});
            setShowEditor(false);
            setIsLoading(false);
          }
        } catch (error) {
          setIsServerValid(false);
          setIsLoading(false);
          setSubmitErrors({ "*": SUBMIT_ERROR });
        }
      },
    [updateExperiment],
  );

  return {
    ...params,
    onSubmit: onSubmit(params, refetch),
    showEditor,
    setShowEditor,
    isLoading,
    submitErrors,
    setSubmitErrors,
    isServerValid,
  };
};

export default useTakeaways;
