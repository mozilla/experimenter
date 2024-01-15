/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useContext, useState } from "react";
import AppLayoutWithExperiment from "src/components/AppLayoutWithExperiment";
import FormAudience from "src/components/PageEditAudience/FormAudience";
import { UPDATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "src/lib/constants";
import { ExperimentContext } from "src/lib/contexts";
import { editCommonRedirects, getStatus } from "src/lib/experiment";
import {
  updateExperiment,
  updateExperimentVariables,
} from "src/types/updateExperiment";

const PageEditAudience: React.FunctionComponent<RouteComponentProps> = () => {
  const { experiment, refetch, useRedirectCondition } =
    useContext(ExperimentContext)!;
  useRedirectCondition(editCommonRedirects);

  const [updateExperimentAudience, { loading }] = useMutation<
    updateExperiment,
    updateExperimentVariables
  >(UPDATE_EXPERIMENT_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const [isServerValid, setIsServerValid] = useState(true);

  const onFormSubmit = useCallback(
    async (
      {
        channel,
        firefoxMinVersion,
        firefoxMaxVersion,
        targetingConfigSlug,
        populationPercent,
        totalEnrolledClients,
        proposedEnrollment,
        proposedDuration,
        proposedReleaseDate,
        countries,
        locales,
        languages,
        isSticky,
        isFirstRun,
        requiredExperimentsBranches,
        excludedExperimentsBranches,
      }: Record<string, any>,
      next: boolean,
    ) => {
      try {
        // issue #3954: Need to parse string IDs into numbers
        const nimbusExperimentId = experiment.id;
        const releaseDate =
          isFirstRun && proposedReleaseDate !== "" ? proposedReleaseDate : null;

        const result = await updateExperimentAudience({
          variables: {
            input: {
              id: nimbusExperimentId,
              changelogMessage: CHANGELOG_MESSAGES.UPDATED_AUDIENCE,
              channel,
              firefoxMinVersion,
              firefoxMaxVersion,
              targetingConfigSlug,
              populationPercent,
              totalEnrolledClients,
              proposedEnrollment,
              proposedDuration,
              proposedReleaseDate: releaseDate,
              countries,
              locales,
              languages,
              isSticky,
              isFirstRun,
              requiredExperimentsBranches,
              excludedExperimentsBranches,
            },
          },
        });

        if (!result.data?.updateExperiment) {
          throw new Error(SUBMIT_ERROR);
        }

        const { message } = result.data.updateExperiment;

        if (message && message !== "success" && typeof message === "object") {
          setIsServerValid(false);
          return void setSubmitErrors(message);
        } else {
          setIsServerValid(true);
          setSubmitErrors({});
          // In practice this should be defined by the time we get here
          refetch();

          if (next) {
            if (getStatus(experiment).live) {
              navigate("summary");
            } else {
              navigate("../");
            }
          }
        }
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [updateExperimentAudience, experiment, refetch],
  );

  return (
    <AppLayoutWithExperiment title="Audience" testId="PageEditAudience">
      <FormAudience
        {...{
          experiment,
          submitErrors,
          setSubmitErrors,
          isServerValid,
          isLoading: loading,
          onSubmit: onFormSubmit,
        }}
      />
    </AppLayoutWithExperiment>
  );
};

export default PageEditAudience;
