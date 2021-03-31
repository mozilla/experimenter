/* istanbul ignore file until EXP-1055 & EXP-1062 done */
/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import { FormProvider } from "react-hook-form";
import { useCommonForm } from "../../hooks";
import { REQUIRED_FIELD } from "../../lib/constants";

export const rejectReasonFieldNames = ["reason"];
type RejectReasonFieldNames = typeof rejectReasonFieldNames[number];

const FormRejectReason = ({
  isLoading,
  onSubmit,
  onCancel,
}: {
  isLoading: boolean;
  onSubmit: (fields: { reason: string }) => void;
  onCancel: () => void;
}) => {
  const isServerValid = true;
  const submitErrors = {};
  const setSubmitErrors = () => {};

  const defaultValues = {
    reason: "",
  };
  type DefaultValues = typeof defaultValues;

  const {
    FormErrors,
    formControlAttrs,
    formMethods,
    handleSubmit,
  } = useCommonForm<RejectReasonFieldNames>(
    defaultValues,
    isServerValid,
    submitErrors,
    setSubmitErrors,
  );

  const handleSubmitClick = handleSubmit(
    (data: DefaultValues) => !isLoading && onSubmit(data),
  );

  return (
    <Alert variant="warning">
      <FormProvider {...formMethods}>
        <Form className="text-body">
          <p>
            <strong>You are rejecting this review.</strong> Please add some
            comments:
          </p>
          <Form.Group controlId="reason">
            <Form.Control
              {...formControlAttrs("reason", REQUIRED_FIELD)}
              as="textarea"
              rows={4}
            />
            <FormErrors name="reason" />
          </Form.Group>
          <div className="d-flex bd-highlight">
            <div>
              <Button
                data-testid="reject-submit"
                className="mr-2 btn btn-danger"
                disabled={isLoading}
                onClick={handleSubmitClick}
              >
                Reject
              </Button>
              <Button
                data-testid="reject-cancel"
                className="btn btn-secondary"
                disabled={isLoading}
                onClick={onCancel}
              >
                Cancel
              </Button>
            </div>
          </div>
        </Form>
      </FormProvider>
    </Alert>
  );
};

export default FormRejectReason;
