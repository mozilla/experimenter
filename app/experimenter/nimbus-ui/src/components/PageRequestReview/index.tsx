/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useRef, useState } from "react";
import { useMutation } from "@apollo/client";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import { SUBMIT_ERROR } from "../../lib/constants";
import { UPDATE_EXPERIMENT_STATUS_MUTATION } from "../../gql/experiments";
import {
  ExperimentInput,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import { updateExperimentStatus_updateExperiment as UpdateExperimentStatus } from "../../types/updateExperimentStatus";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import FormRequestReview from "../FormRequestReview";
import Summary from "../Summary";
import { getStatus } from "../../lib/experiment";

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
    { updateExperiment: UpdateExperimentStatus },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_STATUS_MUTATION);

  const onLaunchClicked = useCallback(async () => {
    try {
      const result = await submitForReview({
        variables: {
          input: {
            id: currentExperiment.current!.id,
            status: NimbusExperimentStatus.REVIEW,
          },
        },
      });

      if (!result.data?.updateExperiment) {
        throw new Error(SUBMIT_ERROR);
      }

      const { message } = result.data.updateExperiment;

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
      redirect={({ status, review }) => {
        if (review && status.draft && !review.ready) {
          // If the experiment is not ready to be reviewed, let's send them to
          // the first page we know needs fixing up, with field errors displayed
          return `edit/${review.invalidPages[0] || "overview"}?show-errors`;
        }

        if (status.released) {
          return "design";
        }
      }}
    >
      {({ experiment }) => {
        currentExperiment.current = experiment;
        const status = getStatus(experiment);

        return (
          <>
            <Summary {...{ experiment }} />

            {(submitSuccess || status.review) && (
              <p className="my-5" data-testid="in-review-label">
                All set! Your experiment is now <b>waiting for review</b>.
              </p>
            )}

            {!submitSuccess && status.draft && (
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
