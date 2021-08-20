/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import { Alert, Button } from "react-bootstrap";

const EndExperiment = ({
  onSubmit,
  isLoading,
}: {
  isLoading: boolean;
  onSubmit: () => void;
}) => {
  const [showEndConfirmation, setShowEndConfirmation] = useState(false);

  const toggleShowEndConfirmation = useCallback(
    () => setShowEndConfirmation(!showEndConfirmation),
    [showEndConfirmation, setShowEndConfirmation],
  );

  return (
    <div className="mb-4" data-testid="experiment-end">
      {showEndConfirmation ? (
        <Alert variant="secondary" data-testid="end-experiment-alert">
          <p>
            Are you sure you want to end your experiment? It will turn off the
            experiment for all users in production.
          </p>

          <div>
            <Button
              variant="primary"
              onClick={onSubmit}
              className="end-experiment-confirm-button"
              disabled={isLoading}
              data-testid="end-experiment-confirm"
            >
              Yes, end the experiment
            </Button>

            <Button
              variant="secondary"
              className="ml-2"
              onClick={toggleShowEndConfirmation}
              disabled={isLoading}
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
          className="end-experiment-start-button"
          disabled={isLoading}
          data-testid="end-experiment-start"
        >
          End Experiment
        </Button>
      )}
    </div>
  );
};

export default EndExperiment;
