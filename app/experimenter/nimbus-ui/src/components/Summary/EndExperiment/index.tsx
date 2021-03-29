/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import React, { useCallback, useState } from "react";
import { Alert, Button } from "react-bootstrap";
import { UPDATE_EXPERIMENT_MUTATION } from "../../../gql/experiments";
import { SUBMIT_ERROR } from "../../../lib/constants";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import {
  ExperimentInput,
  NimbusExperimentStatus,
} from "../../../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperimentEndResult } from "../../../types/updateExperiment";

const EndExperiment = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [showEndConfirmation, setShowEndConfirmation] = useState(false);
  const [endRequested, setEndRequested] = useState(false);
  const isEnding =
    (experiment.status === NimbusExperimentStatus.LIVE &&
      experiment.isEndRequested) ||
    endRequested;

  const [endExperiment, { loading: endExperimentLoading }] = useMutation<
    { updateExperiment: UpdateExperimentEndResult },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  const toggleShowEndConfirmation = useCallback(
    () => setShowEndConfirmation(!showEndConfirmation),
    [showEndConfirmation, setShowEndConfirmation],
  );

  const onConfirmEndClicked = useCallback(async () => {
    try {
      const result = await endExperiment({
        variables: {
          input: {
            id: experiment.id,
            isEndRequested: true,
          },
        },
      });

      if (
        !result.data?.updateExperiment ||
        result.data.updateExperiment.message !== "success"
      ) {
        throw new Error(SUBMIT_ERROR);
      }

      setEndRequested(true);
    } catch (error) {
      setSubmitError(SUBMIT_ERROR);
    }
  }, [experiment, endExperiment, setEndRequested]);

  if (submitError) {
    return (
      <Alert
        className="mb-4"
        variant="warning"
        data-testid="experiment-end-error"
      >
        {submitError}
      </Alert>
    );
  }

  return (
    <div className="mb-4" data-testid="experiment-end">
      {isEnding ? (
        <Alert variant="warning" data-testid="experiment-ended-alert">
          Users will no longer see the experiment once ending is approved in
          Remote Settings, and is in &quot;Complete&quot; state.
        </Alert>
      ) : (
        <>
          {showEndConfirmation ? (
            <Alert variant="warning" data-testid="end-experiment-alert">
              <p>
                Are you sure you want to end your experiment? It will turn off
                the experiment for all users in production.
              </p>

              <div>
                <Button
                  variant="primary"
                  onClick={onConfirmEndClicked}
                  disabled={endExperimentLoading}
                  data-testid="end-experiment-confirm"
                >
                  Yes, end the experiment
                </Button>

                <Button
                  variant="secondary"
                  className="ml-2"
                  onClick={toggleShowEndConfirmation}
                  disabled={endExperimentLoading}
                  data-testid="end-experiment-cancel"
                >
                  Cancel
                </Button>
              </div>
            </Alert>
          ) : (
            <Button
              variant="primary"
              onClick={toggleShowEndConfirmation}
              data-testid="end-experiment-start"
            >
              End Experiment
            </Button>
          )}
        </>
      )}
    </div>
  );
};

export default EndExperiment;
