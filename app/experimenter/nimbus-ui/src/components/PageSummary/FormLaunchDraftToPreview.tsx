/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";
import LinkExternal from "src/components/LinkExternal";
import { ReactComponent as ExternalIcon } from "src/images/external.svg";
import { EXTERNAL_URLS } from "src/lib/constants";

const FormLaunchDraftToPreview = ({
  isLoading,
  onSubmit,
  onLaunchWithoutPreview,
}: {
  isLoading: boolean;
  onSubmit: () => void;
  onLaunchWithoutPreview: () => void;
}) => {
  return (
    <Alert variant="secondary">
      <Form className="text-body">
        <p>
          Do you want to test this experiment before launching to production?{" "}
          <LinkExternal href={EXTERNAL_URLS.PREVIEW_LAUNCH_DOC}>
            <span className="mr-1">Learn more</span>
            <ExternalIcon />
          </LinkExternal>
        </p>

        <div className="d-flex bd-highlight">
          <div>
            <button
              data-testid="launch-draft-to-preview"
              id="launch-to-preview-button"
              type="button"
              className="mr-2 btn btn-primary"
              disabled={isLoading}
              onClick={onSubmit}
            >
              Launch to Preview
            </button>
            <button
              data-testid="start-launch-draft-to-review"
              id="launch-to-review-button"
              type="button"
              className="btn btn-secondary"
              disabled={isLoading}
              onClick={onLaunchWithoutPreview}
            >
              Request Launch without Preview
            </button>
          </div>
        </div>
      </Form>
    </Alert>
  );
};

export default FormLaunchDraftToPreview;
