/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useContext, useState } from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "../../lib/constants";
import { ExperimentContext } from "../../lib/contexts";
import { editCommonRedirects } from "../../lib/experiment";
import { ExperimentInput } from "../../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperimentAudienceResult } from "../../types/updateExperiment";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import FormAudience from "./FormAudience";

const PageEditAudience: React.FunctionComponent<RouteComponentProps> = () => {
  const { experiment, refetch, useRedirectCondition } =
    useContext(ExperimentContext)!;
  useRedirectCondition(editCommonRedirects);

  const [updateExperimentAudience, { loading }] = useMutation<
    { updateExperiment: UpdateExperimentAudienceResult },
    { input: ExperimentInput }
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
        countries,
        locales,
        languages,
        isSticky,
        isFirstRun,
      }: Record<string, any>,
      next: boolean,
    ) => {
      try {
        // issue #3954: Need to parse string IDs into numbers
        const nimbusExperimentId = experiment.id;
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
              countries,
              locales,
              languages,
              isSticky,
              isFirstRun,
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
            navigate("../");
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
