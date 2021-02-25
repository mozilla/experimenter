/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { RouteComponentProps } from "@reach/router";
import React, { useCallback, useMemo, useRef, useState } from "react";
import Alert from "react-bootstrap/Alert";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { ReactComponent as Check } from "../../images/check.svg";
import { SUBMIT_ERROR } from "../../lib/constants";
import { getStatus } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  ExperimentInput,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperiment } from "../../types/updateExperiment";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import Summary from "../Summary";
import FormLaunchDraftToPreview from "./FormLaunchDraftToPreview";
import FormLaunchDraftToReview from "./FormLaunchDraftToReview";
import FormLaunchPreviewToReview from "./FormLaunchPreviewToReview";

const PageRequestReview = ({
  polling = true,
}: {
  polling?: boolean;
} & RouteComponentProps) => {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const currentExperiment = useRef<getExperiment_experimentBySlug>();
  const refetchReview = useRef<() => void>();

  const [updateExperiment, { loading }] = useMutation<
    { updateExperiment: UpdateExperiment },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  const [showLaunchDraftToReview, setShowLaunchDraftToReview] = useState(false);

  const toggleShowLaunchDraftToReview = useCallback(
    () => setShowLaunchDraftToReview(!showLaunchDraftToReview),
    [showLaunchDraftToReview, setShowLaunchDraftToReview],
  );

  const [
    onLaunchToPreviewClicked,
    onBackToDraftClicked,
    onLaunchClicked,
  ] = useMemo(
    () =>
      [
        NimbusExperimentStatus.PREVIEW,
        NimbusExperimentStatus.DRAFT,
        NimbusExperimentStatus.REVIEW,
      ].map((status: NimbusExperimentStatus) => async () => {
        try {
          setSubmitError(null);

          const result = await updateExperiment({
            variables: {
              input: {
                id: currentExperiment.current!.id,
                status,
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

          refetchReview.current!();
          setShowLaunchDraftToReview(false);
        } catch (error) {
          setSubmitError(SUBMIT_ERROR);
        }
      }),
    [updateExperiment, currentExperiment],
  );

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
          // Return to the experiment root/summary page
          return "";
        }
      }}
    >
      {({ experiment, review }) => {
        currentExperiment.current = experiment;
        refetchReview.current = review.refetch;
        const status = getStatus(experiment);

        return (
          <>
            {submitError && (
              <Alert data-testid="submit-error" variant="warning">
                {submitError}
              </Alert>
            )}
            {status.review && (
              <Alert
                data-testid="submit-success"
                variant="success"
                className="bg-transparent text-success"
              >
                <p className="my-1" data-testid="in-review-label">
                  <Check className="align-top" /> All set! Your experiment will
                  launch as soon as it is approved.
                </p>
              </Alert>
            )}
            {status.draft &&
              (showLaunchDraftToReview ? (
                <FormLaunchDraftToReview
                  {...{
                    isLoading: loading,
                    onSubmit: onLaunchClicked,
                    onCancel: toggleShowLaunchDraftToReview,
                    onLaunchToPreview: onLaunchToPreviewClicked,
                  }}
                />
              ) : (
                <FormLaunchDraftToPreview
                  {...{
                    isLoading: loading,
                    onSubmit: onLaunchToPreviewClicked,
                    onLaunchWithoutPreview: toggleShowLaunchDraftToReview,
                  }}
                />
              ))}
            {status.preview && (
              <FormLaunchPreviewToReview
                {...{
                  isLoading: loading,
                  onSubmit: onLaunchClicked,
                  onBackToDraft: onBackToDraftClicked,
                }}
              />
            )}
            <Summary {...{ experiment }} />
          </>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageRequestReview;
