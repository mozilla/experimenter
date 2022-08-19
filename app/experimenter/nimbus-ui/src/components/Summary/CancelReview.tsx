/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import { Alert, Button } from "react-bootstrap";

const CancelReview = ({
  onSubmit,
  isLoading,
}: {
  isLoading: boolean;
  onSubmit: () => void;
}) => {
  const [showCancelConfirmation, setShowCancelConfirmation] = useState(false);

  const toggleShowCancelConfirmation = useCallback(
    () => setShowCancelConfirmation(!showCancelConfirmation),
    [showCancelConfirmation, setShowCancelConfirmation],
  );

  return (
    <div className="mb-4" data-testid="review-cancel">
      {showCancelConfirmation ? (
        <Alert variant="secondary" data-testid="cancel-review-alert">
          <p>Are you sure you want to Cancel Review for your experiment?</p>

          <div>
            <Button
              variant="primary"
              onClick={onSubmit}
              disabled={isLoading}
              data-testid="cancel-review-confirm"
            >
              Yes, Cancel Review Request
            </Button>

            <Button
              variant="secondary"
              className="ml-2"
              onClick={toggleShowCancelConfirmation}
              disabled={isLoading}
              data-testid="cancel-review-cancel"
            >
              Cancel
            </Button>
          </div>
        </Alert>
      ) : (
        <Button
          variant="primary"
          onClick={toggleShowCancelConfirmation}
          disabled={isLoading}
          data-testid="cancel-review-start"
        >
          Cancel Review Request
        </Button>
      )}
    </div>
  );
};

export default CancelReview;
