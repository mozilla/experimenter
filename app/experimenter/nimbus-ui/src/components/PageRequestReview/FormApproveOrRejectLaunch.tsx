/* istanbul ignore file until EXP-1055 & EXP-1062 done */
/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";

const FormApproveOrRejectLaunch = ({
  launchRequestedByUsername,
  isLoading,
  onApprove,
  onReject,
}: {
  launchRequestedByUsername: string;
  isLoading: boolean;
  onApprove: () => void;
  onReject: () => void;
}) => {
  return (
    <Alert variant="warning">
      <Form className="text-body">
        <p>
          <strong>{launchRequestedByUsername}</strong> requested to launch this
          experiment.
        </p>

        <div className="d-flex bd-highlight">
          <div>
            <Button
              data-testid="approve-and-launch"
              className="mr-2 btn btn-success"
              disabled={isLoading}
              onClick={onApprove}
            >
              Approve and Launch
            </Button>
            <Button
              data-testid="reject-launch"
              className="btn btn-danger"
              disabled={isLoading}
              onClick={onReject}
            >
              Reject
            </Button>
          </div>
        </div>
      </Form>
    </Alert>
  );
};

export default FormApproveOrRejectLaunch;
