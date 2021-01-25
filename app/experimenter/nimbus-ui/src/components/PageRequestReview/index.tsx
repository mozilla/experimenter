/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { RouteComponentProps } from "@reach/router";
import React, { useCallback, useRef, useState } from "react";
import Alert from "react-bootstrap/Alert";
import { UPDATE_EXPERIMENT_STATUS_MUTATION } from "../../gql/experiments";
import { useConfig } from "../../hooks/useConfig";
import { ReactComponent as Check } from "../../images/check.svg";
import { SUBMIT_ERROR } from "../../lib/constants";
import { getStatus } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  ExperimentInput,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import { updateExperimentStatus_updateExperiment as UpdateExperimentStatus } from "../../types/updateExperimentStatus";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import Summary from "../Summary";
import FormLaunchDraftToPreview from "./FormLaunchDraftToPreview";
import FormLaunchDraftToReview from "./FormLaunchDraftToReview";
import FormLaunchPreviewToReview from "./FormLaunchPreviewToReview";
import FormRequestReview from "./FormRequestReview";

const PageRequestReview = ({
  polling = true,
  /* istanbul ignore next until EXP-866 final */
  onBackToDraft = () => {},
  /* istanbul ignore next until EXP-866 final */
  onLaunchToReview = () => {},
  /* istanbul ignore next until EXP-866 final */
  onLaunchToPreview = () => {},
}: {
  polling?: boolean;
  /* istanbul ignore next until EXP-866 final */
  onBackToDraft?: () => void;
  /* istanbul ignore next until EXP-866 final */
  onLaunchToReview?: () => void;
  /* istanbul ignore next until EXP-866 final */
  onLaunchToPreview?: () => void;
} & RouteComponentProps) => {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);
  const currentExperiment = useRef<getExperiment_experimentBySlug>();

  const [submitForReview, { loading: submitForReviewLoading }] = useMutation<
    { updateExperiment: UpdateExperimentStatus },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_STATUS_MUTATION);
  const { featureFlags } = useConfig();

  /* istanbul ignore next until EXP-866 final */
  const [showLaunchDraftToReview, setShowLaunchDraftToReview] = useState(false);

  /* istanbul ignore next until EXP-866 final */
  const toggleShowLaunchDraftToReview = useCallback(
    () => setShowLaunchDraftToReview(!showLaunchDraftToReview),
    [showLaunchDraftToReview, setShowLaunchDraftToReview],
  );

  /* istanbul ignore next until EXP-866 final */
  const [mockLoading, setMockLoading] = useState(false);

  /* istanbul ignore next until EXP-866 final */
  const loading = submitForReviewLoading || mockLoading;

  /* istanbul ignore next until EXP-866 final */
  const fakeSubmission = (andThen: Function) => () => {
    setMockLoading(true);
    setTimeout(() => {
      setMockLoading(false);
      setSubmitSuccess(true);
      andThen();
    }, 1000);
  };

  /* istanbul ignore next until EXP-866 final */
  const onLaunchToPreviewClicked = fakeSubmission(onLaunchToPreview);

  /* istanbul ignore next until EXP-866 final */
  const onLaunchToReviewClicked = fakeSubmission(onLaunchToReview);

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
            {
              /* istanbul ignore next */ featureFlags.exp866Preview && (
                <>
                  {submitError && (
                    <Alert data-testid="submit-error" variant="warning">
                      {submitError}
                    </Alert>
                  )}

                  {(submitSuccess || status.review) && (
                    <Alert
                      data-testid="submit-success"
                      variant="success"
                      className="bg-transparent text-success"
                    >
                      <p className="my-1" data-testid="in-review-label">
                        <Check className="align-top" /> All set! Your experiment
                        will launch as soon as it is approved.
                      </p>
                    </Alert>
                  )}

                  {!submitSuccess &&
                    status.draft &&
                    (showLaunchDraftToReview ? (
                      <FormLaunchDraftToReview
                        {...{
                          isLoading: loading,
                          onSubmit: onLaunchToReviewClicked,
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

                  {!submitSuccess && status.preview && (
                    <FormLaunchPreviewToReview
                      {...{
                        isLoading: loading,
                        onSubmit: onLaunchToReviewClicked,
                        onBackToDraft,
                      }}
                    />
                  )}
                </>
              )
            }

            <Summary {...{ experiment }} />

            {!featureFlags.exp866Preview && (
              <>
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
            )}
          </>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageRequestReview;
