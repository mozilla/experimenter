/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback } from "react";
import { Card, Table } from "react-bootstrap";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";
import InlineErrorIcon from "../../../src/components/InlineErrorIcon";
import { useCommonForm } from "../../../src/hooks";

export const TestCases: React.FunctionComponent = ({ children }) => (
  <Table>
    <thead>
      <tr>
        <th className="w-50">Test Steps</th>
        <th>Expected</th>
      </tr>
    </thead>
    <tbody>{children}</tbody>
  </Table>
);

type ProtoFormProps = {
  demoInputs: Array<{
    name: string;
    label: string;
    defaultValue: string;
    required?: boolean;
    requiredAtLaunch?: boolean;
  }>;
  isLoading: boolean;
  isServerValid: boolean;
  submitErrors: Record<string, string[]>;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  reviewMessages: Record<string, string[]>;
  onSubmit: (data: Record<string, any>, reset: Function) => void;
};

export const ProtoForm = ({
  demoInputs,
  isLoading,
  isServerValid,
  onSubmit,
  submitErrors,
  setSubmitErrors,
  reviewMessages,
}: ProtoFormProps) => {
  const defaultValues: Record<string, string> = {};
  demoInputs.forEach(
    ({ name, defaultValue }) => (defaultValues[name] = defaultValue),
  );

  const {
    FormErrors,
    formControlAttrs,
    isValid,
    handleSubmit,
    reset,
    isSubmitted,
    getValues,
  } = useCommonForm(
    defaultValues,
    isServerValid,
    submitErrors,
    setSubmitErrors,
    reviewMessages,
  );

  const handleSubmitAfterValidation = useCallback(
    (data: Record<string, any>) => {
      if (isLoading) return;
      onSubmit(data, reset);
    },
    [isLoading, onSubmit, reset],
  );

  return (
    <Card className="mb-4">
      <Card.Header>Example Form</Card.Header>
      <Card.Body>
        <Form
          noValidate
          onSubmit={handleSubmit(handleSubmitAfterValidation)}
          validated={isSubmitted && isValid}
        >
          {submitErrors["*"] && (
            <Alert data-testid="submit-error" variant="warning">
              {submitErrors["*"]}
            </Alert>
          )}
          {demoInputs.map(
            ({ name, label, required = false, requiredAtLaunch }) => (
              <Form.Group key={name} controlId={name}>
                <Form.Label>
                  {label}

                  {requiredAtLaunch && !getValues(name) && (
                    <InlineErrorIcon
                      field={name}
                      message={`A valid ${label} must be set`}
                    />
                  )}
                </Form.Label>
                <Form.Control
                  {...formControlAttrs(name, { required })}
                  type="text"
                />
                <FormErrors name={name} />
              </Form.Group>
            ),
          )}

          <div className="p-2">
            <button
              data-testid="submit-button"
              type="submit"
              onClick={handleSubmit(handleSubmitAfterValidation)}
              className="btn btn-primary"
              disabled={isLoading}
            >
              {isLoading ? <span>Saving</span> : <span>Save</span>}
            </button>
          </div>
        </Form>
      </Card.Body>
    </Card>
  );
};
