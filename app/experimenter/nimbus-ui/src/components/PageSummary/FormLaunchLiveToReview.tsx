/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";
import FormLaunchConfirmationCheckboxes from "./FormLaunchConfirmationCheckboxes";

const FormLaunchLiveToReview = ({
  isLoading,
  onSubmit,
  onCancel,
}: {
  isLoading: boolean;
  onSubmit: () => void;
  onCancel: () => void;
}) => {
  const [allBoxesChecked, setAllBoxesChecked] = useState(false);

  return (
    <Alert variant="secondary" id="request-launch-alert">
      <Form className="text-body">
        <FormLaunchConfirmationCheckboxes onChange={setAllBoxesChecked} />

        <div className="d-flex bd-highlight">
          <div className="py-1">
            <button
              data-testid="launch-draft-to-review"
              id="request-launch-button"
              type="button"
              className="mr-2 btn btn-primary"
              disabled={isLoading || !allBoxesChecked}
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
