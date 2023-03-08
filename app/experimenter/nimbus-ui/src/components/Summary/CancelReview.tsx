/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Button } from "react-bootstrap";

const CancelReview = ({
  onSubmit,
  isLoading,
}: {
  isLoading: boolean;
  onSubmit: () => void;
}) => {
  return (
    <div className="mb-4" data-testid="review-cancel">
      <Button
        variant="primary"
        onClick={onSubmit}
        disabled={isLoading}
        data-testid="cancel-review-start"
      >
        Cancel Review
      </Button>
    </div>
  );
};

export default CancelReview;
