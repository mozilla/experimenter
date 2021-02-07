/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useContext } from "react";
import { UPDATE_EXPERIMENT_BRANCHES_MUTATION } from "../../gql/experiments";
import { useConfig } from "../../hooks";
import { EXTERNAL_URLS } from "../../lib/constants";
import { ExperimentContext } from "../../lib/contexts";
import { editCommonRedirects } from "../../lib/experiment";
import { ExperimentInput } from "../../types/globalTypes";
import { updateExperimentBranches_updateExperiment as UpdateExperimentBranchesResult } from "../../types/updateExperimentBranches";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import LinkExternal from "../LinkExternal";
import FormBranches from "./FormBranches";
import { FormBranchesSaveState } from "./FormBranches/reducer";

export const SUBMIT_ERROR_MESSAGE = "Save failed, no error available";

const PageEditBranches: React.FunctionComponent<RouteComponentProps> = () => (
  <AppLayoutWithExperiment
    title="Branches"
    testId="PageEditBranches"
    redirect={editCommonRedirects}
  >
    <PageContents />
  </AppLayoutWithExperiment>
);

const PageContents = () => {
  const { experiment } = useContext(ExperimentContext);
  const { featureConfig } = useConfig();

  const [updateExperimentBranches, { loading }] = useMutation<
    { updateExperiment: UpdateExperimentBranchesResult },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_BRANCHES_MUTATION);

  const onFormSave = useCallback(
    async (
      {
        featureConfigId,
        referenceBranch,
        treatmentBranches,
      }: FormBranchesSaveState,
      setSubmitErrors,
      clearSubmitErrors,
    ) => {
      try {
        // issue #3954: Need to parse string IDs into numbers
        const nimbusExperimentId = experiment!.id;
        const result = await updateExperimentBranches({
          variables: {
            input: {
              id: nimbusExperimentId,
              featureConfigId,
              referenceBranch,
              treatmentBranches,
            },
          },
        });

        if (!result.data?.updateExperiment) {
          throw new Error(SUBMIT_ERROR_MESSAGE);
        }

        const { message } = result.data.updateExperiment;

        if (message !== "success" && typeof message === "object") {
          return void setSubmitErrors(message);
        }
        clearSubmitErrors();
      } catch (error) {
        setSubmitErrors({ "*": [error.message] });
      }
    },
    [updateExperimentBranches, experiment],
  );

  const onFormNext = useCallback(() => {
    navigate("metrics");
  }, []);

  return (
    <>
      <p>
        If you want, you can add a <strong>feature flag</strong> configuration
        to each branch. Experiments can only change one flag at a time.{" "}
        <LinkExternal
          href={EXTERNAL_URLS.BRANCHES_GOOGLE_DOC}
          data-testid="learn-more-link"
        >
          Learn more
        </LinkExternal>
      </p>
      <FormBranches
        {...{
          // TODO: EXP-560 - configs should be filtered by application type
          featureConfig,
          isLoading: loading,
          onSave: onFormSave,
          onNext: onFormNext,
        }}
      />
    </>
  );
};

export default PageEditBranches;
