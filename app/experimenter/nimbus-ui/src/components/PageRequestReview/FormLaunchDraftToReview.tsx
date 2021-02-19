/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";
import { ReactComponent as AlertCircle } from "../../images/alert-circle.svg";
import FormLaunchConfirmationCheckboxes from "./FormLaunchConfirmationCheckboxes";

const FormLaunchDraftToReview = ({
  isLoading,
  onLaunchToPreview,
  onSubmit,
  onCancel,
}: {
  isLoading: boolean;
  onLaunchToPreview: () => void;
  onSubmit: () => void;
  onCancel: () => void;
}) => {
  const [allBoxesChecked, setAllBoxesChecked] = useState(false);
  const handleLaunchToPreviewClick = useCallback(
    (ev) => {
      ev.preventDefault();
      onLaunchToPreview();
    },
    [onLaunchToPreview],
  );

  return (
    <Alert variant="warning">
      <Form className="text-body">
        <p className="my-1">
          <span className="text-danger">
            <AlertCircle /> We recommend previewing before launch.
          </span>{" "}
          <button
            data-testid="launch-to-preview-instead"
            type="button"
            className="btn btn-sm btn-primary"
            onClick={handleLaunchToPreviewClick}
          >
            Launch to Preview Now
          </button>
        </p>

        <FormLaunchConfirmationCheckboxes onChange={setAllBoxesChecked} />

        <div className="d-flex bd-highlight">
          <div className="py-1">
            <button
              data-testid="launch-draft-to-review"
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

export default FormLaunchDraftToReview;
