/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useContext, useState } from "react";
import AppLayoutWithExperiment from "src/components/AppLayoutWithExperiment";
import LinkExternal from "src/components/LinkExternal";
import FormMetrics from "src/components/PageEditMetrics/FormMetrics";
import { UPDATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
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

const PageEditMetrics: React.FunctionComponent<RouteComponentProps> = () => {
  const { experiment, refetch, useRedirectCondition } =
    useContext(ExperimentContext)!;
  useRedirectCondition(editCommonRedirects);

  const [updateExperimentOutcomes, { loading }] = useMutation<
    updateExperiment,
    updateExperimentVariables
  >(UPDATE_EXPERIMENT_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const [isServerValid, setIsServerValid] = useState(true);

  const onSave = useCallback(
    async (
      { primaryOutcomes, secondaryOutcomes }: Record<string, string[]>,
      next: boolean,
    ) => {
      try {
        const nimbusExperimentId = experiment.id;
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
          refetch();

          if (next) {
            navigate("audience");
          }
        }
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [updateExperimentOutcomes, experiment, refetch],
  );

  return (
    <AppLayoutWithExperiment title="Metrics" testId="PageEditMetrics">
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
          experiment,
          isLoading: loading,
          isServerValid,
          submitErrors,
          setSubmitErrors,
          onSave,
        }}
      />
    </AppLayoutWithExperiment>
  );
};

export default PageEditMetrics;
