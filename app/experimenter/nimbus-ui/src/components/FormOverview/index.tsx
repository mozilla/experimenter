/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useEffect } from "react";
import { useForm } from "react-hook-form";
import Form from "react-bootstrap/Form";
import Alert from "react-bootstrap/Alert";
import { getExperiment } from "../../types/getExperiment";
import { useExitWarning } from "../../hooks";
import { useConfig } from "../../hooks/useConfig";

type FormOverviewProps = {
  isLoading: boolean;
  isServerValid: boolean;
  submitErrors: Record<string, string[]>;
  experiment?: getExperiment["experimentBySlug"];
  onSubmit: (data: Record<string, any>, reset: Function) => void;
  onCancel?: (ev: React.FormEvent) => void;
  onNext?: (ev: React.FormEvent) => void;
};

const FormOverview = ({
  isLoading,
  isServerValid,
  submitErrors,
  experiment,
  onSubmit,
  onCancel,
  onNext,
}: FormOverviewProps) => {
  const { handleSubmit, register, reset, errors, formState } = useForm({
    mode: "onTouched",
  });
  const { isSubmitted, isDirty, touched } = formState;
  const { application, hypothesisDefault } = useConfig();
  const isValid = isServerValid && formState.isValid;
  const isDirtyUnsaved = isDirty && !(isValid && isSubmitted);

  const shouldWarnOnExit = useExitWarning();
  useEffect(() => {
    shouldWarnOnExit(isDirtyUnsaved);
  }, [shouldWarnOnExit, isDirtyUnsaved]);

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
      onCancel!(ev);
    },
    [onCancel],
  );

  const handleNext = useCallback(
    (ev: React.FormEvent) => {
      ev.preventDefault();
      onNext!(ev);
    },
    [onNext],
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
      data-testid="FormOverview"
    >
      {submitErrors["*"] && (
        <Alert data-testid="submit-error" variant="warning">
          {submitErrors["*"]}
        </Alert>
      )}

      <Form.Group controlId="name">
        <Form.Label>Public name</Form.Label>
        <Form.Control
          {...nameValidated("name")}
          type="text"
          defaultValue={experiment?.name || ""}
          autoFocus={!experiment}
        />
        <Form.Text className="text-muted">
          This name will be public to users in about:studies.
        </Form.Text>
        <FormErrors name="name" />
      </Form.Group>

      <Form.Group controlId="hypothesis">
        <Form.Label>Hypothesis</Form.Label>
        <Form.Control
          {...nameValidated("hypothesis")}
          as="textarea"
          rows={5}
          defaultValue={experiment?.hypothesis || (hypothesisDefault as string)}
        />
        <Form.Text className="text-muted">
          You can add any supporting documents here.
        </Form.Text>
        <FormErrors name="hypothesis" />
      </Form.Group>
      <Form.Group controlId="application">
        <Form.Label>Application</Form.Label>
        {experiment ? (
          <Form.Control
            as="input"
            value={
              application!.find((a) => a?.value === experiment.application)
                ?.label as string
            }
            readOnly
          ></Form.Control>
        ) : (
          <Form.Control {...nameValidated("application")} as="select">
            <option value="">Select...</option>
            {application!.map((app, idx) => (
              <option key={`application-${idx}`} value={app!.value as string}>
                {app!.label}
              </option>
            ))}
          </Form.Control>
        )}
        <Form.Text className="text-muted">
          <p className="mb-0">
            Experiments can only target one Application at a time.
          </p>
          <p>Application can not be changed after an experiment is created.</p>
        </Form.Text>
        <FormErrors name="application" />
      </Form.Group>

      {experiment && (
        <Form.Group controlId="publicDescription">
          <Form.Label>Public description</Form.Label>
          <Form.Control
            ref={register}
            name="publicDescription"
            as="textarea"
            rows={3}
            defaultValue={experiment?.publicDescription as string}
          />
          <Form.Text className="text-muted">
            This description will be public to users on about:studies
          </Form.Text>
          <FormErrors name="publicDescription" />
        </Form.Group>
      )}

      <div className="d-flex flex-row-reverse bd-highlight">
        {onNext && (
          <div className="p-2">
            <button
              onClick={handleNext}
              className="btn btn-secondary"
              disabled={isLoading}
              data-sb-kind="pages/EditBranches"
            >
              Next
            </button>
          </div>
        )}
        <div className="p-2">
          <button
            data-testid="submit-button"
            type="submit"
            onClick={handleSubmit(handleSubmitAfterValidation)}
            className="btn btn-primary"
            disabled={isLoading}
            data-sb-kind="pages/EditOverview"
          >
            {isLoading ? (
              <span>{experiment ? "Saving" : "Submitting"}</span>
            ) : (
              <span>{experiment ? "Save" : "Create experiment"}</span>
            )}
          </button>
        </div>
        {onCancel && (
          <div className="p-2">
            <button onClick={handleCancel} className="btn btn-light">
              Cancel
            </button>
          </div>
        )}
      </div>
    </Form>
  );
};

export default FormOverview;
