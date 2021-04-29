/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useRef, useState } from "react";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "../../lib/constants";
import { editCommonRedirects } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { ExperimentInput } from "../../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperimentOverviewResult } from "../../types/updateExperiment";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import FormOverview from "../FormOverview";

type PageEditOverviewProps = {} & RouteComponentProps;

const PageEditOverview: React.FunctionComponent<PageEditOverviewProps> = () => {
  const [updateExperimentOverview, { loading }] = useMutation<
    { updateExperiment: UpdateExperimentOverviewResult },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  const refetchReview = useRef<() => void>();
  const [isServerValid, setIsServerValid] = useState(true);

  const onFormSubmit = useCallback(
    async (
      {
        name,
        hypothesis,
        riskMitigationLink,
        publicDescription,
        documentationLinks,
      }: Record<string, any>,
      next: boolean,
    ) => {
      try {
        const result = await updateExperimentOverview({
          variables: {
            input: {
              id: currentExperiment.current!.id,
              changelogMessage: CHANGELOG_MESSAGES.UPDATED_OVERVIEW,
              name,
              hypothesis,
              publicDescription,
              riskMitigationLink,
              documentationLinks,
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
          // In practice this should be defined by the time we get here
          refetchReview.current!();

          if (next) {
            navigate(`branches`);
          }
        }
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [updateExperimentOverview, currentExperiment],
  );

  return (
    <AppLayoutWithExperiment
      title="Overview"
      testId="PageEditOverview"
      redirect={editCommonRedirects}
    >
      {({ experiment, review }) => {
        currentExperiment.current = experiment;
        refetchReview.current = review.refetch;

        const { isMissingField } = review;

        return (
          <FormOverview
            {...{
              isLoading: loading,
              isServerValid,
              isMissingField,
              experiment,
              submitErrors,
              setSubmitErrors,
              onSubmit: onFormSubmit,
            }}
          />
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageEditOverview;
