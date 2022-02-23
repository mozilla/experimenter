/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useContext } from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { useConfig } from "../../hooks";
import {
  CHANGELOG_MESSAGES,
  EXTERNAL_URLS,
  SUBMIT_ERROR,
} from "../../lib/constants";
import { ExperimentContext } from "../../lib/contexts";
import { editCommonRedirects } from "../../lib/experiment";
import { ExperimentInput } from "../../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperimentBranchesResult } from "../../types/updateExperiment";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import LinkExternal from "../LinkExternal";
import FormBranches from "./FormBranches";
import { FormBranchesSaveState } from "./FormBranches/reducer";

const PageEditBranches: React.FunctionComponent<RouteComponentProps> = () => {
  const { allFeatureConfigs } = useConfig();
  const { experiment, refetch, useRedirectCondition } =
    useContext(ExperimentContext)!;
  useRedirectCondition(editCommonRedirects);

  const [updateExperimentBranches, { loading }] = useMutation<
    { updateExperiment: UpdateExperimentBranchesResult },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  const applicationFeatureConfigs =
    allFeatureConfigs?.filter(
      (config) => config?.application === experiment.application,
    ) || [];

  const onFormSave = useCallback(
    async (
      {
        featureConfigIds,
        warnFeatureSchema,
        referenceBranch,
        treatmentBranches,
      }: FormBranchesSaveState,
      setSubmitErrors,
      clearSubmitErrors,
      next: boolean,
    ) => {
      try {
        // issue #3954: Need to parse string IDs into numbers
        const nimbusExperimentId = experiment.id;
        const result = await updateExperimentBranches({
          variables: {
            input: {
              id: nimbusExperimentId,
              changelogMessage: CHANGELOG_MESSAGES.UPDATED_BRANCHES,
              featureConfigIds,
              warnFeatureSchema,
              referenceBranch,
              treatmentBranches,
            },
          },
        });

        if (!result.data?.updateExperiment) {
          throw new Error(SUBMIT_ERROR);
        }

        const { message } = result.data.updateExperiment;

        if (message !== "success" && typeof message === "object") {
          return void setSubmitErrors(message);
        }
        refetch();
        clearSubmitErrors();

        if (next) {
          navigate("metrics");
        }
      } catch (error: any) {
        setSubmitErrors({ "*": [error.message] });
      }
    },
    [updateExperimentBranches, experiment, refetch],
  );

  return (
    <AppLayoutWithExperiment title="Branches" testId="PageEditBranches">
      <p>
        You must select a <strong>feature</strong> configuration for your
        experiment. Experiments can only change one feature at a time.{" "}
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
          allFeatureConfigs: applicationFeatureConfigs,
          isLoading: loading,
          onSave: onFormSave,
        }}
      />
    </AppLayoutWithExperiment>
  );
};

export default PageEditBranches;
