/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useContext } from "react";
import AppLayoutWithExperiment from "src/components/AppLayoutWithExperiment";
import LinkExternal from "src/components/LinkExternal";
import FormBranches from "src/components/PageEditBranches/FormBranches";
import { FormBranchesSaveState } from "src/components/PageEditBranches/FormBranches/reducer";
import { UPDATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
import { useConfig } from "src/hooks";
import {
  CHANGELOG_MESSAGES,
  EXTERNAL_URLS,
  SUBMIT_ERROR,
} from "src/lib/constants";
import { ExperimentContext } from "src/lib/contexts";
import { editCommonRedirects } from "src/lib/experiment";
import {
  updateExperiment,
  updateExperimentVariables,
} from "src/types/updateExperiment";

const PageEditBranches: React.FunctionComponent<RouteComponentProps> = () => {
  const { allFeatureConfigs } = useConfig();
  const { experiment, refetch, useRedirectCondition } =
    useContext(ExperimentContext)!;
  useRedirectCondition(editCommonRedirects);

  const [updateExperimentBranches, { loading }] = useMutation<
    updateExperiment,
    updateExperimentVariables
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
        isRollout,
        isLocalized,
        localizations,
        referenceBranch,
        treatmentBranches,
        preventPrefConflicts,
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
              isRollout,
              isLocalized,
              localizations,
              referenceBranch,
              treatmentBranches,
              preventPrefConflicts,
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
        You must select at least one <strong>feature</strong> configuration for
        your experiment.{" "}
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
