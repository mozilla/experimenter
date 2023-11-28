/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";
import FormLaunchConfirmationCheckboxes from "src/components/PageSummary/FormLaunchConfirmationCheckboxes";
import { ReactComponent as Check } from "src/images/check.svg";

const FormLaunchPreviewToReview = ({
  isLoading,
  onSubmit,
  onBackToDraft,
}: {
  isLoading: boolean;
  onSubmit: () => void;
  onBackToDraft: () => void;
}) => {
  const [allBoxesChecked, setAllBoxesChecked] = useState(false);

  return (
    <>
      <Alert
        data-testid="submit-success"
        variant="success"
        className="bg-transparent text-success"
      >
        <p className="my-1" data-testid="in-preview-label">
          <Check className="align-top" /> All set! Your experiment is in Preview
          mode and you can test it now.
        </p>
      </Alert>

      <Alert variant="secondary">
        <Form className="text-body">
          <p className="my-1">
            This experiment is currently <strong>live for testing</strong>, but
            you will need to let QA know in your PI request. When you have
            received a sign-off, click “Request launch” to launch the
            experiment.{" "}
            <strong>
              Note: It can take up to an hour before clients receive a preview
              experiment.
            </strong>
          </p>

          <FormLaunchConfirmationCheckboxes onChange={setAllBoxesChecked} />

          <div className="d-flex bd-highlight">
            <div className="py-2">
              <button
                data-testid="launch-preview-to-review"
                type="button"
                className="mr-3 btn btn-primary"
                disabled={isLoading || !allBoxesChecked}
                onClick={onSubmit}
              >
                Request Launch
              </button>
              <button
                data-testid="launch-preview-to-draft"
                type="button"
                className="btn btn-secondary"
                disabled={isLoading}
                onClick={onBackToDraft}
              >
                Go Back to Draft
              </button>
            </div>
          </div>
        </Form>
      </Alert>
    </>
  );
};

export default FormLaunchPreviewToReview;
