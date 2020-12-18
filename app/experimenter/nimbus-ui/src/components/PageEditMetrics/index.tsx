/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { navigate, RouteComponentProps } from "@reach/router";
import { useMutation } from "@apollo/client";
import React, { useState, useRef, useCallback } from "react";

import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { SUBMIT_ERROR } from "../../lib/constants";
import { UPDATE_EXPERIMENT_PROBESETS_MUTATION } from "../../gql/experiments";
import { updateExperimentProbeSets_updateExperimentProbeSets as UpdateExperimentProbeSetsResult } from "../../types/updateExperimentProbeSets";
import { UpdateExperimentProbeSetsInput } from "../../types/globalTypes";
import { useConfig } from "../../hooks/useConfig";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import FormMetrics from "../FormMetrics";
import LinkExternal from "../LinkExternal";
import { editCommonRedirects } from "../../lib/experiment";

export const CORE_METRICS_DOC_URL =
  "https://docs.google.com/document/d/155EUgzn22VTX8mFwesSROT3Z6JORSfb5VyoMoLra7ws/edit#heading=h.uq23fsvh16rc";

const PageEditMetrics: React.FunctionComponent<RouteComponentProps> = () => {
  const { probeSets } = useConfig();

  const [updateExperimentProbeSets, { loading }] = useMutation<
    { updateExperimentProbeSets: UpdateExperimentProbeSetsResult },
    { input: UpdateExperimentProbeSetsInput }
  >(UPDATE_EXPERIMENT_PROBESETS_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  const refetchReview = useRef<() => void>();
  const [isServerValid, setIsServerValid] = useState(true);

  const onSave = useCallback(
    async ({
      primaryProbeSetIds,
      secondaryProbeSetIds,
    }: Record<string, number[]>) => {
      try {
        const nimbusExperimentId = parseInt(currentExperiment.current!.id, 10);
        const result = await updateExperimentProbeSets({
          variables: {
            input: {
              nimbusExperimentId,
              primaryProbeSetIds,
              secondaryProbeSetIds,
            },
          },
        });

        if (!result.data?.updateExperimentProbeSets) {
          throw new Error("Save failed, no error available");
        }

        const { message } = result.data.updateExperimentProbeSets;

        if (message && message !== "success" && typeof message === "object") {
          setIsServerValid(false);
          return void setSubmitErrors(message);
        } else {
          setIsServerValid(true);
          setSubmitErrors({});
          // In practice this should be defined by the time we get here
          refetchReview.current!();
        }
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [updateExperimentProbeSets, currentExperiment],
  );

  const onNext = useCallback(() => {
    navigate("audience");
  }, []);

  return (
    <AppLayoutWithExperiment
      title="Metrics"
      testId="PageEditMetrics"
      redirect={editCommonRedirects}
    >
      {({ experiment, review }) => {
        currentExperiment.current = experiment;
        refetchReview.current = review.refetch;

        return (
          <>
            <p>
              Every experiment analysis automatically includes how your
              experiment has impacted{" "}
              <strong>Retention, Search Count, and Ad Click</strong> metrics.
              Get more information on{" "}
              <LinkExternal
                href={CORE_METRICS_DOC_URL}
                data-testid="core-metrics-link"
              >
                Core Firefox Metrics
              </LinkExternal>
              .
            </p>
            <FormMetrics
              {...{
                experiment,
                probeSets,
                isLoading: loading,
                isServerValid,
                submitErrors,
                onSave,
                onNext,
              }}
            />
          </>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageEditMetrics;
