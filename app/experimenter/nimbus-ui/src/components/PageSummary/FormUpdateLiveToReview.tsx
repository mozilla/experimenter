/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";

const FormUpdateLiveToReview = ({
  isLoading,
  onSubmit,
  onRevert,
}: {
  isLoading: boolean;
  onSubmit: () => void;
  onRevert: () => void;
}) => {
  return (
    <Alert
      variant="secondary"
      id="request-live-update-alert"
      data-testid="request-live-update-alert"
    >
      <Form className="text-body">
        <div className="d-flex bd-highlight">
          <div className="py-1">
            <p>Review and update live rollout:</p>
            <button
              data-testid="update-live-to-review"
              id="request-update-button"
              type="button"
              className="mr-2 btn btn-primary"
              disabled={isLoading}
              onClick={onSubmit}
            >
              Request Update
            </button>
            <button
              data-testid="revert"
              type="button"
              className="btn btn-secondary"
              disabled={true}
              onClick={onRevert}
            >
              Revert update
            </button>
          </div>
        </div>
      </Form>
    </Alert>
  );
};

export default FormUpdateLiveToReview;
