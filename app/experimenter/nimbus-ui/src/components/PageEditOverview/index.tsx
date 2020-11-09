/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useRef, useState } from "react";
import { navigate, RouteComponentProps } from "@reach/router";
import FormOverview from "../FormOverview";
import AppLayoutWithSidebarAndData from "../AppLayoutWithSidebarAndData";
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

  const onFormSubmit = useCallback(
    async (
      { name, hypothesis, application, publicDescription }: Record<string, any>,
      resetForm: Function,
    ) => {
      try {
        const result = await updateExperimentOverview({
          variables: {
            input: {
              id: currentExperiment.current!.id,
              name,
              hypothesis,
              application,
              publicDescription,
            },
          },
        });

        if (!result.data?.updateExperimentOverview) {
          throw new Error("Save failed, no error available");
        }

        const { message } = result.data.updateExperimentOverview;

        if (message !== "success" && typeof message === "object") {
          return void setSubmitErrors(message);
        }

        resetForm({ name, hypothesis, application, publicDescription });
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
    <AppLayoutWithSidebarAndData title="Overview" testId="PageEditOverview">
      {({ experiment }) => {
        currentExperiment.current = experiment;

        return (
          <FormOverview
            {...{
              isLoading: loading,
              experiment,
              submitErrors,
              onSubmit: onFormSubmit,
              onNext: onFormNext,
            }}
          />
        );
      }}
    </AppLayoutWithSidebarAndData>
  );
};

export default PageEditOverview;
