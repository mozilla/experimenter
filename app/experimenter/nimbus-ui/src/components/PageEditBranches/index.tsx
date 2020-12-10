/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useRef } from "react";
import { navigate, RouteComponentProps } from "@reach/router";
import { useConfig } from "../../hooks";
import FormBranches from "../FormBranches";
import { FormBranchesSaveState } from "../FormBranches/reducer";
import LinkExternal from "../LinkExternal";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import { useMutation } from "@apollo/client";
import { UPDATE_EXPERIMENT_BRANCHES_MUTATION } from "../../gql/experiments";
import { UpdateExperimentBranchesInput } from "../../types/globalTypes";
import { updateExperimentBranches_updateExperimentBranches as UpdateExperimentBranchesResult } from "../../types/updateExperimentBranches";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

// TODO: EXP-656 find this doco URL
const BRANCHES_DOC_URL =
  "https://mana.mozilla.org/wiki/pages/viewpage.action?spaceKey=FJT&title=Project+Nimbus";

export const SUBMIT_ERROR_MESSAGE = "Save failed, no error available";

const PageEditBranches: React.FunctionComponent<RouteComponentProps> = () => {
  const { featureConfig } = useConfig();

  const [updateExperimentBranches, { loading }] = useMutation<
    { updateExperimentBranches: UpdateExperimentBranchesResult },
    { input: UpdateExperimentBranchesInput }
  >(UPDATE_EXPERIMENT_BRANCHES_MUTATION);

  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  const refetchReview = useRef<() => void>();

  const onFormSave = useCallback(
    async (
      {
        featureConfigId,
        referenceBranch,
        treatmentBranches,
      }: FormBranchesSaveState,
      setSubmitErrors,
      clearSubmitErrors,
    ) => {
      try {
        // issue #3954: Need to parse string IDs into numbers
        const nimbusExperimentId = parseInt(currentExperiment.current!.id, 10);
        const result = await updateExperimentBranches({
          variables: {
            input: {
              nimbusExperimentId,
              featureConfigId,
              referenceBranch,
              treatmentBranches,
            },
          },
        });

        if (!result.data?.updateExperimentBranches) {
          throw new Error(SUBMIT_ERROR_MESSAGE);
        }

        const { message } = result.data.updateExperimentBranches;

        if (message !== "success" && typeof message === "object") {
          return void setSubmitErrors(message);
        }

        clearSubmitErrors();
      } catch (error) {
        setSubmitErrors({ "*": [error.message] });
      }
    },
    [updateExperimentBranches],
  );

  const onFormNext = useCallback(() => {
    navigate("metrics");
  }, []);

  return (
    <AppLayoutWithExperiment title="Branches" testId="PageEditBranches">
      {({ experiment, review }) => {
        currentExperiment.current = experiment;
        refetchReview.current = review.refetch;

        const { isMissingField } = review;
        const applicationFeatureConfigs =
          featureConfig?.filter(
            (config) => config?.application === experiment.application,
          ) || [];

        return (
          <>
            <p>
              If you want, you can add a <strong>feature flag</strong>{" "}
              configuration to each branch. Experiments can only change one flag
              at a time.{" "}
              <LinkExternal href={BRANCHES_DOC_URL}>Learn more</LinkExternal>
            </p>
            <FormBranches
              {...{
                experiment,
                featureConfig: applicationFeatureConfigs,
                isMissingField,
                isLoading: loading,
                onSave: onFormSave,
                onNext: onFormNext,
              }}
            />
          </>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageEditBranches;
