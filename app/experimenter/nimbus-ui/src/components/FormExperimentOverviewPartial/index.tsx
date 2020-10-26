/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback } from "react";
import { useForm } from "react-hook-form";
import Form from "react-bootstrap/Form";
import Alert from "react-bootstrap/Alert";

type FormExperimentOverviewPartialProps = {
  isLoading: boolean;
  submitErrors: Record<string, string[]>;
  onSubmit: (data: Record<string, any>, reset: Function) => void;
  onCancel: (ev: React.FormEvent) => void;
  applications: string[];
};

const FormExperimentOverviewPartial = ({
  isLoading,
  submitErrors,
  onSubmit,
  onCancel,
  applications,
}: FormExperimentOverviewPartialProps) => {
  const { handleSubmit, register, reset, errors, formState } = useForm({
    mode: "onTouched",
  });
  const { isSubmitted, isValid, isDirty, touched } = formState;

  const handleSubmitAfterValidation = useCallback(
    (data: Record<string, any>) => {
      if (isLoading) return;
      onSubmit(data, reset);
    },
    [isLoading, onSubmit, reset],
  );

  const handleCancel = useCallback(
    (ev: React.FormEvent) => {
      ev.preventDefault();
      onCancel(ev);
    },
    [onCancel],
  );

  const nameValidated = (
    name: string,
    // This could be ValidationRules from react-hook-form/validator, but
    // register() has several signatures and only this one produces a ref
    validateRule: Parameters<typeof register>[1] = {
      required: "This field may not be blank.",
    },
  ) => ({
    name,
    isInvalid: !!submitErrors[name] || (touched[name] && errors[name]),
    isValid: !submitErrors[name] && touched[name] && !errors[name],
    ref: register(validateRule),
  });

  const FormErrors = ({ name }: { name: string }) => (
    <>
      {errors[name] && (
        <Form.Control.Feedback type="invalid" data-for={name}>
          {errors[name].message}
        </Form.Control.Feedback>
      )}
      {submitErrors[name] && (
        <Form.Control.Feedback type="invalid" data-for={name}>
          {submitErrors[name]}
        </Form.Control.Feedback>
      )}
    </>
  );

  return (
    <Form
      noValidate
      onSubmit={handleSubmit(handleSubmitAfterValidation)}
      validated={isSubmitted && isValid}
      data-testid="FormExperimentOverviewPartial"
    >
      {submitErrors["*"] && (
        <Alert data-testid="submit-error" variant="warning">
          {submitErrors["*"]}
        </Alert>
      )}

      <Form.Group controlId="name">
        <Form.Label>Public name</Form.Label>
        <Form.Control {...nameValidated("name")} type="text" autoFocus />
        <Form.Text className="text-muted">
          This name will be public to users in about:studies.
        </Form.Text>
        <FormErrors name="name" />
      </Form.Group>

      <Form.Group controlId="hypothesis">
        <Form.Label>Hypothesis</Form.Label>
        <Form.Control {...nameValidated("hypothesis")} as="textarea" rows={3} />
        <Form.Text className="text-muted">
          You can add any supporting documents here.
        </Form.Text>
        <FormErrors name="hypothesis" />
      </Form.Group>

      <Form.Group controlId="application">
        <Form.Label>Application</Form.Label>
        <Form.Control {...nameValidated("application")} as="select">
          <option value="">Select...</option>
          {applications.map((application, idx) => (
            <option key={`application-${idx}`}>{application}</option>
          ))}
        </Form.Control>
        <Form.Text className="text-muted">
          Experiments can only target one Application at a time.
        </Form.Text>
        <FormErrors name="application" />
      </Form.Group>

      <div className="d-flex flex-row-reverse bd-highlight">
        <div className="p-2">
          <button
            data-testid="submit-button"
            type="submit"
            onClick={handleSubmit(handleSubmitAfterValidation)}
            className="btn btn-primary"
            disabled={isLoading || !isDirty || !isValid}
            data-sb-kind="pages/EditOverview"
          >
            {isLoading ? (
              <span>Submitting</span>
            ) : (
              <span>Create experiment</span>
            )}
          </button>
        </div>
        <div className="p-2">
          <button onClick={handleCancel} className="btn btn-light">
            Cancel
          </button>
        </div>
      </div>
    </Form>
  );
};

export default FormExperimentOverviewPartial;
