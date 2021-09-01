/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import { useNavigate } from "@reach/router";
import React, { useState } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import Modal from "react-bootstrap/Modal";
import { FormProvider } from "react-hook-form";
import { CLONE_EXPERIMENT_MUTATION } from "../../../gql/experiments";
import { useCommonForm } from "../../../hooks";
import { BASE_PATH, SUBMIT_ERROR } from "../../../lib/constants";
import { cloneExperiment_cloneExperiment } from "../../../types/cloneExperiment";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import { ExperimentCloneInput } from "../../../types/globalTypes";
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
          <Form noValidate onSubmit={handleSave} data-testid="FormClone">
            {submitErrors["*"] && (
              <Alert data-testid="submit-error" variant="warning">
                {submitErrors["*"]}
              </Alert>
            )}
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

export const useCloneDialog = (experiment: getExperiment_experimentBySlug) => {
  const navigate = useNavigate();

  const [show, setShowDialog] = useState(false);
  const onShow = () => setShowDialog(true);
  const onCancel = () => setShowDialog(false);

  const [cloneExperiment] = useMutation<
    { cloneExperiment: cloneExperiment_cloneExperiment },
    { input: ExperimentCloneInput }
  >(CLONE_EXPERIMENT_MUTATION);

  const [isLoading, cloneSetIsLoading] = useState(false);
  const [isServerValid, cloneSetIsServerValid] = useState(true);
  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});

  const onSave = async (data: CloneParams) => {
    cloneSetIsLoading(true);
    cloneSetIsServerValid(true);
    setSubmitErrors({});
    try {
      const result = await cloneExperiment({
        variables: {
          input: {
            parentSlug: experiment.slug,
            name: data.name,
          },
        },
      });

      // istanbul ignore next - can't figure out how to trigger this in a test
      if (!result.data?.cloneExperiment) {
        throw new Error(SUBMIT_ERROR);
      }

      const { message } = result.data.cloneExperiment;
      if (message && message !== "success" && typeof message === "object") {
        cloneSetIsServerValid(false);
        setSubmitErrors(message);
      } else {
        const { slug } = result.data.cloneExperiment.nimbusExperiment!;
        navigate(`${BASE_PATH}/${slug}`);
        setShowDialog(false);
      }
    } catch (error) {
      setSubmitErrors({ "*": SUBMIT_ERROR });
    }
    cloneSetIsLoading(false);
  };

  return {
    experiment,
    disabled: isLoading,
    onShow,
    show,
    onCancel,
    onSave,
    isLoading,
    isServerValid,
    submitErrors,
    setSubmitErrors,
  };
};

export default CloneDialog;
