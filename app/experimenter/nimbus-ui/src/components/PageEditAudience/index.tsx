/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useContext, useState } from "react";
import { UPDATE_EXPERIMENT_AUDIENCE_MUTATION } from "../../gql/experiments";
import { SUBMIT_ERROR } from "../../lib/constants";
import { ExperimentContext } from "../../lib/contexts";
import { editCommonRedirects } from "../../lib/experiment";
import { ExperimentInput } from "../../types/globalTypes";
import { updateExperimentAudience_updateExperiment as UpdateExperimentAudienceResult } from "../../types/updateExperimentAudience";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import FormAudience from "./FormAudience";

const PageEditAudience: React.FunctionComponent<RouteComponentProps> = () => (
  <AppLayoutWithExperiment
    title="Audience"
    testId="PageEditAudience"
    redirect={editCommonRedirects}
  >
    <PageContents />
  </AppLayoutWithExperiment>
);

const PageContents = () => {
  const { experiment, refetch } = useContext(ExperimentContext);

  const [updateExperimentAudience, { loading }] = useMutation<
    { updateExperiment: UpdateExperimentAudienceResult },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_AUDIENCE_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const [isServerValid, setIsServerValid] = useState(true);

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
        const nimbusExperimentId = experiment!.id;
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
          refetch();
        }
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [updateExperimentAudience, experiment, refetch],
  );

  const onFormNext = useCallback(() => {
    navigate("../request-review");
  }, []);

  return (
    <FormAudience
      {...{
        submitErrors,
        setSubmitErrors,
        isServerValid,
        isLoading: loading,
        onSubmit: onFormSubmit,
        onNext: onFormNext,
      }}
    />
  );
};

export default PageEditAudience;
