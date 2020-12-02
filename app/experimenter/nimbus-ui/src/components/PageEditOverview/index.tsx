/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useRef, useState } from "react";
import { navigate, RouteComponentProps } from "@reach/router";
import FormOverview from "../FormOverview";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import { useMutation } from "@apollo/client";
import { UPDATE_EXPERIMENT_OVERVIEW_MUTATION } from "../../gql/experiments";
import { SUBMIT_ERROR } from "../../lib/constants";
import { UpdateExperimentInput } from "../../types/globalTypes";
import { updateExperimentOverview_updateExperimentOverview as UpdateExperimentOverviewResult } from "../../types/updateExperimentOverview";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

type PageEditOverviewProps = {} & RouteComponentProps;

const PageEditOverview: React.FunctionComponent<PageEditOverviewProps> = () => {
  const [updateExperimentOverview, { loading }] = useMutation<
    { updateExperimentOverview: UpdateExperimentOverviewResult },
    { input: UpdateExperimentInput }
  >(UPDATE_EXPERIMENT_OVERVIEW_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  const refetchReview = useRef<() => void>();
  const [isServerValid, setIsServerValid] = useState(true);

  const onFormSubmit = useCallback(
    async ({ name, hypothesis, publicDescription }: Record<string, any>) => {
      try {
        const result = await updateExperimentOverview({
          variables: {
            input: {
              id: currentExperiment.current!.id,
              name,
              hypothesis,
              publicDescription,
            },
          },
        });

        if (!result.data?.updateExperimentOverview) {
          throw new Error("Save failed, no error available");
        }

        const { message } = result.data.updateExperimentOverview;

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
    [updateExperimentOverview, currentExperiment],
  );

  const onFormNext = useCallback(() => {
    navigate(`branches`);
  }, []);

  return (
    <AppLayoutWithExperiment title="Overview" testId="PageEditOverview">
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
              onSubmit: onFormSubmit,
              onNext: onFormNext,
            }}
          />
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageEditOverview;
