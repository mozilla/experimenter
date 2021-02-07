/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useContext, useState } from "react";
import { UPDATE_EXPERIMENT_PROBESETS_MUTATION } from "../../gql/experiments";
import { EXTERNAL_URLS, SUBMIT_ERROR } from "../../lib/constants";
import { ExperimentContext } from "../../lib/contexts";
import { editCommonRedirects } from "../../lib/experiment";
import { ExperimentInput } from "../../types/globalTypes";
import { updateExperimentProbeSets_updateExperiment as UpdateExperimentProbeSetsResult } from "../../types/updateExperimentProbeSets";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import LinkExternal from "../LinkExternal";
import FormMetrics from "./FormMetrics";

const PageEditMetrics: React.FunctionComponent<RouteComponentProps> = () => (
  <AppLayoutWithExperiment
    title="Metrics"
    testId="PageEditMetrics"
    redirect={editCommonRedirects}
  >
    <PageContents />
  </AppLayoutWithExperiment>
);

const PageContents = () => {
  const { refetch, experiment } = useContext(ExperimentContext);

  const [updateExperimentProbeSets, { loading }] = useMutation<
    { updateExperiment: UpdateExperimentProbeSetsResult },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_PROBESETS_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const [isServerValid, setIsServerValid] = useState(true);

  const onSave = useCallback(
    async ({
      primaryProbeSetIds,
      secondaryProbeSetIds,
    }: Record<string, number[]>) => {
      try {
        const nimbusExperimentId = experiment!.id;
        const result = await updateExperimentProbeSets({
          variables: {
            input: {
              id: nimbusExperimentId,
              primaryProbeSetIds,
              secondaryProbeSetIds,
            },
          },
        });

        if (!result.data?.updateExperiment) {
          throw new Error("Save failed, no error available");
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
    [updateExperimentProbeSets, experiment, refetch],
  );

  const onNext = useCallback(() => {
    navigate("audience");
  }, []);

  return (
    <>
      <p>
        Every experiment analysis automatically includes how your experiment has
        impacted <strong>Retention, Search Count, and Ad Click</strong> metrics.
        Get more information on{" "}
        <LinkExternal
          href={EXTERNAL_URLS.METRICS_GOOGLE_DOC}
          data-testid="core-metrics-link"
        >
          Core Firefox Metrics
        </LinkExternal>
        .
      </p>
      <FormMetrics
        {...{
          isLoading: loading,
          isServerValid,
          submitErrors,
          setSubmitErrors,
          onSave,
          onNext,
        }}
      />
    </>
  );
};

export default PageEditMetrics;
