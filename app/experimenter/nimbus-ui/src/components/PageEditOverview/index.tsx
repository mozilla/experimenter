/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useContext, useState } from "react";
import { UPDATE_EXPERIMENT_OVERVIEW_MUTATION } from "../../gql/experiments";
import { SUBMIT_ERROR } from "../../lib/constants";
import { ExperimentContext } from "../../lib/contexts";
import { editCommonRedirects } from "../../lib/experiment";
import { ExperimentInput } from "../../types/globalTypes";
import { updateExperimentOverview_updateExperiment as UpdateExperimentOverviewResult } from "../../types/updateExperimentOverview";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import FormOverview from "../FormOverview";

type PageEditOverviewProps = {} & RouteComponentProps;

const PageEditOverview: React.FunctionComponent<PageEditOverviewProps> = () => (
  <AppLayoutWithExperiment
    title="Overview"
    testId="PageEditOverview"
    redirect={editCommonRedirects}
  >
    <PageContents />
  </AppLayoutWithExperiment>
);

const PageContents = () => {
  const { refetch, experiment } = useContext(ExperimentContext);

  const [updateExperimentOverview, { loading }] = useMutation<
    { updateExperiment: UpdateExperimentOverviewResult },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_OVERVIEW_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const [isServerValid, setIsServerValid] = useState(true);

  const onFormSubmit = useCallback(
    async ({
      name,
      hypothesis,
      riskMitigationLink,
      publicDescription,
      documentationLinks,
    }: Record<string, any>) => {
      try {
        const result = await updateExperimentOverview({
          variables: {
            input: {
              id: experiment!.id,
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
          refetch();
        }
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [updateExperimentOverview, experiment, refetch],
  );

  const onFormNext = useCallback(() => {
    navigate(`branches`);
  }, []);

  return (
    <FormOverview
      {...{
        isLoading: loading,
        isServerValid,
        submitErrors,
        setSubmitErrors,
        onSubmit: onFormSubmit,
        onNext: onFormNext,
      }}
    />
  );
};

export default PageEditOverview;
