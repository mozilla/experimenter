/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import { Alert, Button } from "react-bootstrap";

const EndEnrollment = ({
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
    <div className="mb-4" data-testid="enrollment-end">
      {showEndConfirmation ? (
        <Alert variant="secondary" data-testid="end-enrollment-alert">
          <p>Are you sure you want to end enrollment for your experiment?</p>

          <div>
            <Button
              variant="primary"
              onClick={onSubmit}
              disabled={isLoading}
              data-testid="end-enrollment-confirm"
            >
              Yes, end enrollment for the experiment
            </Button>

            <Button
              variant="secondary"
              className="ml-2"
              onClick={toggleShowEndConfirmation}
              disabled={isLoading}
              data-testid="end-enrollment-cancel"
            >
              Cancel
            </Button>
          </div>
        </Alert>
      ) : (
        <Button
          variant="primary"
          onClick={toggleShowEndConfirmation}
          disabled={isLoading}
          data-testid="end-enrollment-start"
        >
          End Enrollment for Experiment
        </Button>
      )}
    </div>
  );
};

export default EndEnrollment;
