/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import Form from "react-bootstrap/Form";

type FormExperimentOverviewPartialProps = {
  onSubmit: SubmitHandler<Record<string, any>>;
  onCancel: (ev: React.FormEvent) => void;
  applications: string[];
};

const FormExperimentOverviewPartial = ({
  onSubmit,
  onCancel,
  applications,
}: FormExperimentOverviewPartialProps) => {
  const { handleSubmit, register, errors, formState } = useForm({
    mode: "onTouched",
  });
  const { isSubmitted, isValid, isDirty, touched } = formState;

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
    validateRule: Parameters<typeof register>[1] = { required: "Required" },
  ) => ({
    name,
    isInvalid: touched[name] && errors[name],
    isValid: touched[name] && !errors[name],
    ref: register(validateRule),
  });

  return (
    <Form
      noValidate
      onSubmit={handleSubmit(onSubmit)}
      validated={isSubmitted && isValid}
      data-testid="FormExperimentOverviewPartial"
    >
      <Form.Group controlId="name">
        <Form.Label>Public name</Form.Label>
        <Form.Control {...nameValidated("name")} type="text" autoFocus />
        <Form.Text className="text-muted">
          This name will be public to users in about:studies.
        </Form.Text>
        <Form.Control.Feedback type="invalid">
          This field may not be blank.
        </Form.Control.Feedback>
      </Form.Group>

      <Form.Group controlId="hypothesis">
        <Form.Label>Hypothesis</Form.Label>
        <Form.Control {...nameValidated("hypothesis")} as="textarea" rows={3} />
        <Form.Text className="text-muted">
          You can add any supporting documents here.
        </Form.Text>
        <Form.Control.Feedback type="invalid">
          This field may not be blank.
        </Form.Control.Feedback>
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
        <Form.Control.Feedback type="invalid">
          This field may not be blank.
        </Form.Control.Feedback>
      </Form.Group>

      <div className="d-flex flex-row-reverse bd-highlight">
        <div className="p-2">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={!isDirty || !isValid}
          >
            Create experiment
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
