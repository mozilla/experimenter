/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useRef, useState } from "react";
import { navigate, RouteComponentProps } from "@reach/router";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import { useMutation } from "@apollo/client";
import { UpdateExperimentAudienceInput } from "../../types/globalTypes";
import { updateExperimentAudience_updateExperimentAudience as UpdateExperimentAudienceResult } from "../../types/updateExperimentAudience";
import { UPDATE_EXPERIMENT_AUDIENCE_MUTATION } from "../../gql/experiments";
import { SUBMIT_ERROR } from "../../lib/constants";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import FormAudience from "../FormAudience";
import { editCommonRedirects } from "../../lib/experiment";

const PageEditAudience: React.FunctionComponent<RouteComponentProps> = () => {
  const [updateExperimentAudience, { loading }] = useMutation<
    { updateExperimentAudience: UpdateExperimentAudienceResult },
    { input: UpdateExperimentAudienceInput }
  >(UPDATE_EXPERIMENT_AUDIENCE_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  const refetchReview = useRef<() => void>();

  const onFormSubmit = useCallback(
    async ({
      channel,
      firefoxMinVersion,
      targetingConfigSlug,
      populationPercent,
      totalEnrolledClients,
      proposedEnrollment,
      proposedDuration,
    }: Record<string, any>) => {
      try {
        // issue #3954: Need to parse string IDs into numbers
        const nimbusExperimentId = parseInt(currentExperiment.current!.id, 10);
        const result = await updateExperimentAudience({
          variables: {
            input: {
              nimbusExperimentId,
              channel,
              firefoxMinVersion,
              targetingConfigSlug,
              populationPercent,
              totalEnrolledClients,
              proposedEnrollment,
              proposedDuration,
            },
          },
        });

        if (!result.data?.updateExperimentAudience) {
          throw new Error(SUBMIT_ERROR);
        }

        const { message } = result.data.updateExperimentAudience;

        if (message && message !== "success" && typeof message === "object") {
          return void setSubmitErrors(message);
        } else {
          setSubmitErrors({});
          // In practice this should be defined by the time we get here
          refetchReview.current!();
        }
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [updateExperimentAudience, currentExperiment],
  );

  const onFormNext = useCallback(() => {
    navigate("../request-review");
  }, []);

  return (
    <AppLayoutWithExperiment
      title="Audience"
      testId="PageEditAudience"
      redirect={editCommonRedirects}
    >
      {({ experiment, review }) => {
        currentExperiment.current = experiment;
        refetchReview.current = review.refetch;

        const { isMissingField } = review;

        return (
          <FormAudience
            {...{
              experiment,
              submitErrors,
              isMissingField,
              isLoading: loading,
              onSubmit: onFormSubmit,
              onNext: onFormNext,
            }}
          />
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageEditAudience;
