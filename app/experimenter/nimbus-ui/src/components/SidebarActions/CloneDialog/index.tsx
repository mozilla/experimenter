/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import Modal from "react-bootstrap/Modal";
import { FormProvider } from "react-hook-form";
import { useCommonForm } from "../../../hooks";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import { SlugTextControl } from "../../SlugTextControl";

type CloneDialogProps = {
  experiment: getExperiment_experimentBySlug;
  show: boolean;
  isLoading: boolean;
  isServerValid: boolean;
  submitErrors: SerializerMessages;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  onCancel: () => void;
  onSave: (params: CloneParams) => void;
};

export type CloneParams = {
  name: string;
};

export const CloneDialog = ({
  show,
  experiment,
  isLoading,
  isServerValid,
  submitErrors,
  setSubmitErrors,
  onCancel,
  onSave,
}: CloneDialogProps) => {
  const defaultValues: CloneParams = {
    name: `${experiment!.name} Copy`,
  };

  const { FormErrors, formControlAttrs, handleSubmit, formMethods, getValues } =
    useCommonForm<keyof CloneParams>(
      defaultValues,
      isServerValid,
      submitErrors,
      setSubmitErrors,
    );

  const { trigger } = formMethods;

  const handleSave = handleSubmit(onSave);

  const nameControlAttrs = formControlAttrs("name");

  const nameOnChange = () => {
    nameControlAttrs.onChange!();
    // HACK: Explicitly trigger update because `mode: "all"` in
    // useReactHookForm() seems to stop after one update
    trigger(["name"]);
  };

  return (
    <Modal show={show} onHide={onCancel} data-testid="CloneDialog">
      <Modal.Header closeButton>
        <Modal.Title>Copy Experiment {experiment.name}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <FormProvider {...formMethods}>
          <Form noValidate onSubmit={handleSave} data-testid="FormOverview">
            <Form.Group controlId="name">
              <Form.Label>Public name</Form.Label>
              <Form.Control
                {...{
                  ...nameControlAttrs,
                  type: "text",
                  onChange: nameOnChange,
                }}
              />
              <Form.Text className="text-muted">
                This name will be public to users in about:studies.
              </Form.Text>
              <FormErrors name="name" />
            </Form.Group>
            <Form.Group controlId="name">
              <Form.Label>Slug</Form.Label>
              <SlugTextControl
                value={getValues("name")}
                defaultValue={defaultValues["name"]}
              />
              <Form.Text className="text-muted">
                This is a unique identifier based on the public name.
              </Form.Text>
              <FormErrors name="name" />
            </Form.Group>
          </Form>
        </FormProvider>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" disabled={isLoading} onClick={onCancel}>
          Cancel
        </Button>
        <Button variant="primary" disabled={isLoading} onClick={handleSave}>
          {isLoading ? "Saving" : "Save"}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default CloneDialog;
