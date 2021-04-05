/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useRef, useState } from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { SUBMIT_ERROR } from "../../lib/constants";
import { editCommonRedirects } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { ExperimentInput } from "../../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperimentAudienceResult } from "../../types/updateExperiment";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import FormAudience from "./FormAudience";

const PageEditAudience: React.FunctionComponent<RouteComponentProps> = () => {
  const [updateExperimentAudience, { loading }] = useMutation<
    { updateExperiment: UpdateExperimentAudienceResult },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  const refetchReview = useRef<() => void>();
  const [isServerValid, setIsServerValid] = useState(true);

  const onFormSubmit = useCallback(
    async (
      {
        channel,
        firefoxMinVersion,
        targetingConfigSlug,
        populationPercent,
        totalEnrolledClients,
        proposedEnrollment,
        proposedDuration,
      }: Record<string, any>,
      next: boolean,
    ) => {
      try {
        // issue #3954: Need to parse string IDs into numbers
        const nimbusExperimentId = currentExperiment.current!.id;
        const result = await updateExperimentAudience({
          variables: {
            input: {
              id: nimbusExperimentId,
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
          refetchReview.current!();

          if (next) {
            navigate("../request-review");
          }
        }
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [updateExperimentAudience, currentExperiment],
  );

  return (
    <AppLayoutWithExperiment
      title="Audience"
      testId="PageEditAudience"
      redirect={editCommonRedirects}
      pageId="PageEditAudience"
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
              setSubmitErrors,
              isMissingField,
              isServerValid,
              isLoading: loading,
              onSubmit: onFormSubmit,
            }}
          />
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageEditAudience;
