/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect, useMemo } from "react";
import { FormProvider, SubmitHandler } from "react-hook-form";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Button from "react-bootstrap/Button";
import Alert from "react-bootstrap/Alert";

import { useExitWarning, useForm } from "../../../hooks";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import {
  getConfig_nimbusConfig,
  getConfig_nimbusConfig_featureConfig,
} from "../../../types/getConfig";

import { useFormBranchesReducer, FormBranchesSaveState } from "./reducer";
import { FormData } from "./reducer/update";
import FormBranch from "./FormBranch";
import { IsDirtyUnsaved } from "../../../hooks/useCommonForm/useCommonFormMethods";

type FormBranchesProps = {
  isLoading: boolean;
  experiment: getExperiment_experimentBySlug;
  featureConfig: getConfig_nimbusConfig["featureConfig"];
  onSave: (
    state: FormBranchesSaveState,
    setSubmitErrors: Function,
    clearSubmitErrors: Function,
  ) => void;
  onNext: () => void;
};

export const FormBranches = ({
  isLoading,
  experiment,
  featureConfig,
  onSave,
  onNext,
}: FormBranchesProps) => {
  const reviewErrors =
    typeof experiment?.readyForReview?.message !== "string"
      ? experiment?.readyForReview?.message
      : null;

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

  const defaultValues = useMemo(
    () => ({
      referenceBranch,
      treatmentBranches,
    }),
    [referenceBranch, treatmentBranches],
  );

  // TODO: EXP-614 submitErrors type is any, but in practical use it's AnnotatedBranch["errors"]
  const setSubmitErrors = (submitErrors: any) =>
    dispatch({ type: "setSubmitErrors", submitErrors });

  const formMethods = useForm(defaultValues);

  const {
    reset,
    getValues,
    handleSubmit,
    formState: { isDirty, isSubmitted, isValid, errors, touched },
  } = formMethods;

  const isDirtyUnsaved = IsDirtyUnsaved(isDirty, isValid, isSubmitted);

  const shouldWarnOnExit = useExitWarning();
  useEffect(() => {
    shouldWarnOnExit(isDirtyUnsaved);
  }, [shouldWarnOnExit, isDirtyUnsaved]);

  // reset the form when defaultValues change, i.e. the reducer updates
  // with submit errors and we need to mark fields as untouched
  useEffect(() => {
    reset(defaultValues);
  }, [defaultValues, reset]);

  const isSaveDisabled = isLoading;
  const isNextDisabled = isLoading;

  const commitFormData = () => {
    dispatch({ type: "commitFormData", formData: getValues() as FormData });
  };

  const clearSubmitErrors = () => dispatch({ type: "clearSubmitErrors" });

  const handleAddBranch = () => {
    commitFormData();
    dispatch({ type: "addBranch" });
  };

  const handleRemoveBranch = (idx: number) => () => {
    commitFormData();
    dispatch({ type: "removeBranch", idx });
  };

  const handleEqualRatioChange = (ev: React.ChangeEvent<HTMLInputElement>) => {
    commitFormData();
    dispatch({ type: "setEqualRatio", value: ev.target.checked });
  };

  // HACK: just use the first available feature config when adding
  // The only available indicator whether to display "Add feature config" is a non-null feature config
  const handleAddFeatureConfig = () => {
    commitFormData();
    dispatch({ type: "setFeatureConfig", value: featureConfig![0] });
  };

  const handleRemoveFeatureConfig = () => {
    commitFormData();
    dispatch({ type: "removeFeatureConfig" });
  };

  const handleFeatureConfigChange = (
    value: getConfig_nimbusConfig_featureConfig | null,
  ) => {
    commitFormData();
    dispatch({ type: "setFeatureConfig", value });
  };

  const handleSubmitWhenValid: SubmitHandler<any> = async (formData) => {
    try {
      commitFormData();
      onSave(extractSaveState(formData), setSubmitErrors, clearSubmitErrors);
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
    equalRatio,
    featureConfig,
    experimentFeatureConfig,
    onFeatureConfigChange: handleFeatureConfigChange,
    onAddFeatureConfig: handleAddFeatureConfig,
    onRemoveFeatureConfig: handleRemoveFeatureConfig,
    setSubmitErrors,
  };

  type FormBranchProps = React.ComponentProps<typeof FormBranch>;

  return (
    <FormProvider {...formMethods}>
      <Form
        data-testid="FormBranches"
        className="border-top my-3"
        noValidate
        onSubmit={handleSubmit(handleSubmitWhenValid)}
      >
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

        <div className="p-2">
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
        </div>

        <section>
          {referenceBranch && (
            <FormBranch
              {...{
                ...commonBranchProps,
                fieldNamePrefix: "referenceBranch",
                // react-hook-form types seem broken for nested fields
                errors: (errors.referenceBranch ||
                  {}) as FormBranchProps["errors"],
                // react-hook-form types seem broken for nested fields
                touched: (touched.referenceBranch ||
                  {}) as FormBranchProps["touched"],
                isReference: true,
                branch: { ...referenceBranch, key: "branch-reference" },
                reviewErrors: reviewErrors?.["reference_branch"],
                defaultValues: defaultValues.referenceBranch || {},
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
                      fieldNamePrefix: `treatmentBranches[${idx}]`,
                      //@ts-ignore react-hook-form types seem broken for nested fields
                      errors: (errors?.treatmentBranches?.[idx] ||
                        {}) as FormBranchProps["errors"],
                      //@ts-ignore react-hook-form types seem broken for nested fields
                      touched: (touched?.treatmentBranches?.[idx] ||
                        {}) as FormBranchProps["touched"],
                      branch,
                      reviewErrors: reviewErrors?.["treatment_branches"]?.[idx],
                      onRemove: handleRemoveBranch(idx),
                      defaultValues:
                        defaultValues.treatmentBranches?.[idx] || {},
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
              onClick={handleSubmit(handleSubmitWhenValid)}
            >
              <span>{isLoading ? "Saving" : "Save"}</span>
            </button>
          </div>
        </div>
      </Form>
    </FormProvider>
  );
};

export default FormBranches;
