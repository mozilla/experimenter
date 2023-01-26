/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";

const FormLaunchLiveToReview = ({
  isLoading,
  onSubmit,
  onCancel,
}: {
  isLoading: boolean;
  onSubmit: () => void;
  onCancel: () => void;
}) => {
  return (
    <Alert
      variant="secondary"
      id="request-live-launch-alert"
      data-testid="request-live-launch-alert"
    >
      <Form className="text-body">
        <div className="d-flex bd-highlight">
          <div className="py-1">
          <p>
          Review and launch live rollout updates:
          </p>
            <button
              data-testid="launch-live-to-review"
              id="request-launch-button"
              type="button"
              className="mr-2 btn btn-primary"
              disabled={isLoading}
              onClick={onSubmit}
            >
              Request Launch
            </button>
            <button
              data-testid="cancel"
              type="button"
              className="btn btn-secondary"
              disabled={isLoading}
              onClick={onCancel}
            >
              Cancel
            </button>
          </div>
        </div>
      </Form>
    </Alert>
  );
};

export default FormLaunchLiveToReview;
