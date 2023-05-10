/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useContext, useState } from "react";
import AppLayoutWithExperiment from "src/components/AppLayoutWithExperiment";
import FormOverview from "src/components/FormOverview";
import { UPDATE_EXPERIMENT_MUTATION } from "src/gql/experiments";
import {
  CHANGELOG_MESSAGES,
  SAVE_FAILED_NO_ERROR,
  SUBMIT_ERROR,
} from "src/lib/constants";
import { ExperimentContext } from "src/lib/contexts";
import { editCommonRedirects } from "src/lib/experiment";
import { optionalStringBool } from "src/lib/utils";
import {
  updateExperiment,
  updateExperimentVariables,
} from "src/types/updateExperiment";

type PageEditOverviewProps = Record<string, any> & RouteComponentProps;

const PageEditOverview: React.FunctionComponent<PageEditOverviewProps> = () => {
  const { experiment, refetch, useRedirectCondition } =
    useContext(ExperimentContext)!;
  useRedirectCondition(editCommonRedirects);

  const [updateExperimentOverview, { loading }] = useMutation<
    updateExperiment,
    updateExperimentVariables
  >(UPDATE_EXPERIMENT_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const [isServerValid, setIsServerValid] = useState(true);

  const onFormSubmit = useCallback(
    async (
      {
        name,
        hypothesis,
        publicDescription,
        documentationLinks,
        riskBrand,
        riskRevenue,
        riskPartnerRelated,
        projects,
        isLocalized,
        localizations,
      }: Record<string, any>,
      next: boolean,
    ) => {
      try {
        const result = await updateExperimentOverview({
          variables: {
            input: {
              id: experiment!.id,
              changelogMessage: CHANGELOG_MESSAGES.UPDATED_OVERVIEW,
              name,
              hypothesis,
              publicDescription,
              documentationLinks,
              projects,
              riskBrand: optionalStringBool(riskBrand),
              riskRevenue: optionalStringBool(riskRevenue),
              riskPartnerRelated: optionalStringBool(riskPartnerRelated),
              isLocalized,
              localizations,
            },
          },
        });

        if (!result.data?.updateExperiment) {
          throw new Error(SAVE_FAILED_NO_ERROR);
        }

        const { message } = result.data.updateExperiment;

        if (message && message !== "success" && typeof message === "object") {
          setIsServerValid(false);
          return void setSubmitErrors(message);
        } else {
          setIsServerValid(true);
          setSubmitErrors({});
          refetch();

          if (next) {
            navigate(`branches`);
          }
        }
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [updateExperimentOverview, experiment, refetch],
  );

  return (
    <AppLayoutWithExperiment title="Overview" testId="PageEditOverview">
      <FormOverview
        {...{
          isLoading: loading,
          isServerValid,
          experiment,
          submitErrors,
          setSubmitErrors,
          onSubmit: onFormSubmit,
        }}
      />
    </AppLayoutWithExperiment>
  );
};

export default PageEditOverview;
