/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";

const FormApproveConfirm = ({
  isLoading,
  onConfirm,
  actionDescription,
}: {
  isLoading: boolean;
  onConfirm: () => void;
  actionDescription: string;
}) => {
  return (
    <Alert variant="secondary">
      <Form className="text-body">
        <p>
          <strong>Action required —</strong> Please review this change in Remote
          Settings to {actionDescription} this experiment
        </p>

        <div className="d-flex bd-highlight">
          <div>
            <Button
              data-testid="open-remote-settings"
              className="mr-2 btn btn-primary"
              disabled={isLoading}
              onClick={onConfirm}
            >
              Open Remote Settings
            </Button>
          </div>
        </div>
      </Form>
    </Alert>
  );
};

export default FormApproveConfirm;
