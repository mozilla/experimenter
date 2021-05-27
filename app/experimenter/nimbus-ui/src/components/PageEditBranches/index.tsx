/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useRef } from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { useConfig } from "../../hooks";
import { CHANGELOG_MESSAGES, EXTERNAL_URLS } from "../../lib/constants";
import { editCommonRedirects } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { ExperimentInput } from "../../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperimentBranchesResult } from "../../types/updateExperiment";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import LinkExternal from "../LinkExternal";
import FormBranches from "./FormBranches";
import { FormBranchesSaveState } from "./FormBranches/reducer";

export const SUBMIT_ERROR_MESSAGE = "Save failed, no error available";

const PageEditBranches: React.FunctionComponent<RouteComponentProps> = () => {
  const { featureConfig } = useConfig();

  const [updateExperimentBranches, { loading }] = useMutation<
    { updateExperiment: UpdateExperimentBranchesResult },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

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
      next: boolean,
    ) => {
      try {
        // issue #3954: Need to parse string IDs into numbers
        const nimbusExperimentId = currentExperiment.current!.id;
        const result = await updateExperimentBranches({
          variables: {
            input: {
              id: nimbusExperimentId,
              changelogMessage: CHANGELOG_MESSAGES.UPDATED_BRANCHES,
              featureConfigId,
              referenceBranch,
              treatmentBranches,
            },
          },
        });

        if (!result.data?.updateExperiment) {
          throw new Error(SUBMIT_ERROR_MESSAGE);
        }

        const { message } = result.data.updateExperiment;

        if (message !== "success" && typeof message === "object") {
          return void setSubmitErrors(message);
        }
        refetchReview.current!();
        clearSubmitErrors();

        if (next) {
          navigate("metrics");
        }
      } catch (error) {
        setSubmitErrors({ "*": [error.message] });
      }
    },
    [updateExperimentBranches, refetchReview],
  );

  return (
    <AppLayoutWithExperiment
      title="Branches"
      testId="PageEditBranches"
      redirect={editCommonRedirects}
    >
      {({ experiment, refetch }) => {
        currentExperiment.current = experiment;
        refetchReview.current = refetch;

        const applicationFeatureConfigs =
          featureConfig?.filter(
            (config) => config?.application === experiment.application,
          ) || [];

        return (
          <>
            <p>
              You must add a <strong>feature flag</strong> configuration to each
              branch. Experiments can only change one flag at a time.{" "}
              <LinkExternal
                href={EXTERNAL_URLS.BRANCHES_GOOGLE_DOC}
                data-testid="learn-more-link"
              >
                Learn more
              </LinkExternal>
            </p>
            <FormBranches
              {...{
                experiment,
                featureConfig: applicationFeatureConfigs,
                isLoading: loading,
                onSave: onFormSave,
              }}
            />
          </>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageEditBranches;
