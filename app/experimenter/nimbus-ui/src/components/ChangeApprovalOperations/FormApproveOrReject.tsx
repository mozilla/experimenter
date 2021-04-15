/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

const FormApproveOrReject = ({
  actionDescription,
  timeoutEvent,
  reviewRequestEvent,
  isLoading,
  onApprove,
  onReject,
}: {
  actionDescription: string;
  timeoutEvent?: getExperiment_experimentBySlug["timeout"];
  reviewRequestEvent?: getExperiment_experimentBySlug["reviewRequest"];
  isLoading: boolean;
  onApprove: () => void;
  onReject: () => void;
}) => {
  const ucActionDescription =
    actionDescription.charAt(0).toUpperCase() + actionDescription.slice(1);
  return (
    <>
      {timeoutEvent && (
        <Alert variant="danger" data-testid="timeout-notice">
          <p className="mb-0">
            <span role="img" aria-label="red X emoji">
              ❌
            </span>{" "}
            Remote Settings request has timed out, please go through the{" "}
            {actionDescription} request and approval flow again.
          </p>
        </Alert>
      )}
      <Alert variant="secondary">
        <Form className="text-body">
          <p>
            <strong>{reviewRequestEvent!.changedBy!.email}</strong> requested to{" "}
            {actionDescription} this experiment.
          </p>

          <div className="d-flex bd-highlight">
            <div>
              <Button
                data-testid="approve-request"
                className="mr-2 btn btn-success"
                disabled={isLoading}
                onClick={onApprove}
              >
                Approve and {ucActionDescription}
              </Button>
              <Button
                data-testid="reject-request"
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
    </>
  );
};

export default FormApproveOrReject;
