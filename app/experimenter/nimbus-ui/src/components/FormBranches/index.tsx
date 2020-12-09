/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useRef, useState, useEffect, useMemo } from "react";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Button from "react-bootstrap/Button";
import Alert from "react-bootstrap/Alert";

import { useExitWarning } from "../../hooks";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  getConfig_nimbusConfig,
  getConfig_nimbusConfig_featureConfig,
} from "../../types/getConfig";

import FormBranch, { FormBranchRegistration } from "./FormBranch";

import {
  useFormBranchesReducer,
  FormBranchesSaveState,
  REFERENCE_BRANCH_IDX,
  AnnotatedBranch,
} from "./reducer";

export const FormBranches = ({
  isLoading,
  experiment,
  featureConfig,
  onSave,
  onNext,
  isMissingField,
}: {
  isLoading: boolean;
  experiment: getExperiment_experimentBySlug;
  featureConfig: getConfig_nimbusConfig["featureConfig"];
  onSave: (
    state: FormBranchesSaveState,
    setSubmitErrors: Function,
    clearSubmitErrors: Function,
  ) => void;
  onNext: () => void;
  isMissingField: (fieldName: string) => boolean;
}) => {
  const [
    {
      featureConfig: experimentFeatureConfig,
      referenceBranch,
      treatmentBranches,
      equalRatio,
      globalErrors,
    },
    extractSaveState,
    dispatch,
  ] = useFormBranchesReducer(experiment);

  const isSaveDisabled = isLoading;
  const isNextDisabled = isLoading;

  const [lastSubmitTime, setLastSubmitTime] = useState<number | undefined>();

  // TODO: submitErrors type is any, but in practical use it's AnnotatedBranch["errors"]
  const setSubmitErrors = (submitErrors: any) =>
    dispatch({ type: "setSubmitErrors", submitErrors });

  const clearSubmitErrors = () => dispatch({ type: "clearSubmitErrors" });

  const handleAddBranch = () => dispatch({ type: "addBranch" });

  const handleRemoveBranch = (idx: number) => () =>
    dispatch({ type: "removeBranch", idx });

  const handleEqualRatioChange = (ev: React.ChangeEvent<HTMLInputElement>) =>
    dispatch({ type: "setEqualRatio", value: ev.target.checked });

  // HACK: just use the first available feature config when adding
  // The only available indicator whether to display "Add feature config" is a non-null feature config
  const handleAddFeatureConfig = () =>
    dispatch({ type: "setFeatureConfig", value: featureConfig![0] });

  const handleRemoveFeatureConfig = () =>
    dispatch({ type: "removeFeatureConfig" });

  const handleFeatureConfigChange = (
    value: getConfig_nimbusConfig_featureConfig | null,
  ) => dispatch({ type: "setFeatureConfig", value });

  const registeredBranchForms = useRef<FormBranchRegistration[]>([]);
  const [registerBranchForm, unregisterBranchForm] = useMemo(() => {
    const currentBranchForms = registeredBranchForms.current;
    return [
      (registration: FormBranchRegistration) => {
        currentBranchForms.push(registration);
      },
      (registration: FormBranchRegistration) => {
        const idx = currentBranchForms.indexOf(registration);
        if (idx !== -1) currentBranchForms.splice(idx, 1);
      },
    ];
  }, [registeredBranchForms]);

  const isDirtyUnsaved = registeredBranchForms.current.some(
    ({ isDirty }) => isDirty,
  );

  const shouldWarnOnExit = useExitWarning();
  useEffect(() => {
    shouldWarnOnExit(isDirtyUnsaved);
  }, [shouldWarnOnExit, isDirtyUnsaved]);

  const handleSaveClick = async (
    ev: React.MouseEvent<HTMLButtonElement, MouseEvent>,
  ) => {
    ev.preventDefault();
    try {
      // form validation is async, so trigger it on all branch forms and
      // collect their values in one batch with Promise.all
      const branchFormValues = await Promise.all(
        registeredBranchForms.current.map(
          async ({ idx, trigger, getValues }) => ({
            idx,
            isValid: await trigger(),
            ...getValues(),
          }),
        ),
      );

      setLastSubmitTime(Date.now());
      dispatch({ type: "commitDirtyBranches", branchFormValues });

      let allValid = branchFormValues.every(({ isValid }) => isValid);
      if (allValid) {
        onSave(
          extractSaveState(branchFormValues),
          setSubmitErrors,
          clearSubmitErrors,
        );
      }
    } catch (error) {
      setSubmitErrors({ "*": [error.message] });
    }
  };

  const handleNextClick = (
    ev: React.MouseEvent<HTMLButtonElement, MouseEvent>,
  ) => {
    ev.preventDefault();
    onNext();
  };

  const commonBranchProps = {
    lastSubmitTime,
    equalRatio,
    featureConfig,
    experimentFeatureConfig,
    registerBranchForm,
    unregisterBranchForm,
    onFeatureConfigChange: handleFeatureConfigChange,
    onAddFeatureConfig: handleAddFeatureConfig,
    onRemoveFeatureConfig: handleRemoveFeatureConfig,
  };

  return (
    <section data-testid="FormBranches" className="border-top my-3">
      {globalErrors?.map((err, idx) => (
        <Alert
          key={`global-error-${idx}`}
          data-testid="global-error"
          variant="warning"
          className="my-2"
        >
          {err}
        </Alert>
      ))}

      <Form className="p-2">
        <Form.Row className="my-3">
          <Form.Group controlId="evenRatio">
            <Form.Check
              data-testid="equal-ratio-checkbox"
              onChange={handleEqualRatioChange}
              checked={equalRatio}
              type="checkbox"
              label="Users should be split evenly between all branches"
            />
          </Form.Group>
          <Form.Group as={Col} className="align-top text-right">
            <Button
              data-testid="add-branch"
              variant="outline-primary"
              size="sm"
              onClick={handleAddBranch}
            >
              + Add branch
            </Button>
          </Form.Group>
        </Form.Row>
      </Form>

      <section>
        {referenceBranch && (
          <FormBranch
            {...{
              ...commonBranchProps,
              id: `branch-reference`,
              idx: REFERENCE_BRANCH_IDX,
              isReference: true,
              branch: { ...referenceBranch, key: "branch-reference" },
              showMissingIcon: isMissingField("reference_branch"),
            }}
          />
        )}
        {treatmentBranches &&
          treatmentBranches.map(
            (branch, idx) =>
              branch && (
                <FormBranch
                  {...{
                    ...commonBranchProps,
                    key: branch.key,
                    id: branch.key,
                    idx,
                    branch,
                    onRemove: handleRemoveBranch(idx),
                  }}
                />
              ),
          )}
      </section>

      <div className="d-flex flex-row-reverse bd-highlight">
        <div className="p-2">
          <button
            data-testid="next-button"
            className="btn btn-secondary"
            disabled={isNextDisabled}
            onClick={handleNextClick}
          >
            Next
          </button>
        </div>
        <div className="p-2">
          <button
            data-testid="save-button"
            type="submit"
            className="btn btn-primary"
            disabled={isSaveDisabled}
            onClick={handleSaveClick}
          >
            <span>{isLoading ? "Saving" : "Save"}</span>
          </button>
        </div>
      </div>
    </section>
  );
};

export default FormBranches;
