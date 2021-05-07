/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useRef, useState } from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import {
  CHANGELOG_MESSAGES,
  EXTERNAL_URLS,
  SUBMIT_ERROR,
} from "../../lib/constants";
import { editCommonRedirects } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { ExperimentInput } from "../../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperimentOutcomesResult } from "../../types/updateExperiment";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import LinkExternal from "../LinkExternal";
import FormMetrics from "./FormMetrics";

const PageEditMetrics: React.FunctionComponent<RouteComponentProps> = () => {
  const [updateExperimentOutcomes, { loading }] = useMutation<
    { updateExperiment: UpdateExperimentOutcomesResult },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  const refetchReview = useRef<() => void>();
  const [isServerValid, setIsServerValid] = useState(true);

  const onSave = useCallback(
    async (
      { primaryOutcomes, secondaryOutcomes }: Record<string, string[]>,
      next: boolean,
    ) => {
      try {
        const nimbusExperimentId = currentExperiment.current!.id;
        const result = await updateExperimentOutcomes({
          variables: {
            input: {
              id: nimbusExperimentId,
              changelogMessage: CHANGELOG_MESSAGES.UPDATED_OUTCOMES,
              primaryOutcomes,
              secondaryOutcomes,
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
            navigate("audience");
          }
        }
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [updateExperimentOutcomes, currentExperiment],
  );

  return (
    <AppLayoutWithExperiment
      title="Metrics"
      testId="PageEditMetrics"
      redirect={editCommonRedirects}
    >
      {({ experiment, refetch }) => {
        currentExperiment.current = experiment;
        refetchReview.current = refetch;

        return (
          <>
            <p>
              Every experiment analysis automatically includes how your
              experiment has impacted{" "}
              <strong>Retention, Search Count, and Ad Click</strong> metrics.
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
                experiment,
                isLoading: loading,
                isServerValid,
                submitErrors,
                setSubmitErrors,
                onSave,
              }}
            />
          </>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageEditMetrics;
