/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useRef, useState } from "react";
import { useMutation } from "@apollo/client";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import TableSummary from "../TableSummary";
import { SUBMIT_ERROR } from "../../lib/constants";
import { UPDATE_EXPERIMENT_STATUS_MUTATION } from "../../gql/experiments";
import {
  UpdateExperimentStatusInput,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import { updateExperimentStatus_updateExperimentStatus as UpdateExperimentStatus } from "../../types/updateExperimentStatus";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import FormRequestReview from "../FormRequestReview";

type PageRequestReviewProps = {
  polling?: boolean;
} & RouteComponentProps;

const PageRequestReview: React.FunctionComponent<PageRequestReviewProps> = ({
  polling = true,
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);
  const currentExperiment = useRef<getExperiment_experimentBySlug>();

  const [submitForReview, { loading }] = useMutation<
    { updateExperimentStatus: UpdateExperimentStatus },
    { input: UpdateExperimentStatusInput }
  >(UPDATE_EXPERIMENT_STATUS_MUTATION);

  const onLaunchClicked = useCallback(async () => {
    try {
      const result = await submitForReview({
        variables: {
          input: {
            nimbusExperimentId: parseInt(currentExperiment.current!.id),
            status: NimbusExperimentStatus.REVIEW,
          },
        },
      });

      if (!result.data?.updateExperimentStatus) {
        throw new Error(SUBMIT_ERROR);
      }

      const { message } = result.data.updateExperimentStatus;

      if (message && message !== "success" && typeof message === "object") {
        return void setSubmitError(message.status.join(", "));
      }

      setSubmitSuccess(true);
    } catch (error) {
      setSubmitError(SUBMIT_ERROR);
    }
  }, [submitForReview, currentExperiment]);

  return (
    <AppLayoutWithExperiment
      title="Review &amp; Launch"
      testId="PageRequestReview"
      {...{ polling }}
    >
      {({ experiment }) => {
        currentExperiment.current = experiment;

        return (
          <>
            <TableSummary {...{ experiment }} />

            {![
              NimbusExperimentStatus.REVIEW,
              NimbusExperimentStatus.DRAFT,
            ].includes(experiment.status!) && (
              <p className="my-5" data-testid="cant-review-label">
                This experiment&apos;s status is{" "}
                <b className="text-lowercase">{experiment.status}</b> and cannot
                be reviewed.
              </p>
            )}

            {(submitSuccess ||
              experiment.status === NimbusExperimentStatus.REVIEW) && (
              <p className="my-5" data-testid="in-review-label">
                All set! Your experiment is now <b>waiting for review</b>.
              </p>
            )}

            {!submitSuccess &&
              experiment.status === NimbusExperimentStatus.DRAFT && (
                <FormRequestReview
                  {...{
                    isLoading: loading,
                    submitError,
                    onSubmit: onLaunchClicked,
                  }}
                />
              )}
          </>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageRequestReview;
