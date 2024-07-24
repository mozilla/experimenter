/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";
import FormLaunchConfirmationCheckboxes from "src/components/PageSummary/FormLaunchConfirmationCheckboxes";
import { ReactComponent as AlertCircle } from "src/images/alert-circle.svg";

const FormLaunchDraftToReview = ({
  isLoading,
  onLaunchToPreview,
  onSubmit,
  onCancel,
  canPublishToPreview,
}: {
  isLoading: boolean;
  onLaunchToPreview: () => void;
  onSubmit: () => void;
  onCancel: () => void;
  canPublishToPreview: boolean;
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
    <Alert variant="secondary" id="request-launch-alert">
      <Form className="text-body">
        {canPublishToPreview ? (
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
        ) : (
          <>
            <p className="my-1">
              <span
                className="text-danger"
                data-testid="cannot-launch-to-preview"
              >
                <AlertCircle /> This experiment cannot be previewed!
              </span>
            </p>
            <p className="my-1">
              This experiment uses features that prevent it from being launched
              to preview. We highly recommend QAing this experiment on stage
              first.
            </p>
          </>
        )}

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

export default FormLaunchDraftToReview;
