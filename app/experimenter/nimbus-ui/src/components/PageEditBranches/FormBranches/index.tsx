/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect, useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import { FormProvider } from "react-hook-form";
import { useExitWarning, useForm, useReviewCheck } from "../../../hooks";
import { IsDirtyUnsaved } from "../../../hooks/useCommonForm/useCommonFormMethods";
import {
  getConfig_nimbusConfig,
  getConfig_nimbusConfig_featureConfigs,
} from "../../../types/getConfig";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import FormBranch from "./FormBranch";
import { FormBranchesSaveState, useFormBranchesReducer } from "./reducer";
import { FormData } from "./reducer/update";

type FormBranchesProps = {
  isLoading: boolean;
  experiment: getExperiment_experimentBySlug;
  featureConfigs: getConfig_nimbusConfig["featureConfigs"];
  onSave: (
    state: FormBranchesSaveState,
    setSubmitErrors: (submitErrors: any) => void,
    clearSubmitErrors: () => void,
    next: boolean,
  ) => void;
};

export const FormBranches = ({
  isLoading,
  experiment,
  featureConfigs,
  onSave,
}: FormBranchesProps) => {
  const { fieldMessages } = useReviewCheck(experiment);

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

  // We show two branches by default, an empty control/reference branch and treatment
  // branch, which are given a default branch name. If a branch slug is not set, it means
  // that branch hasn't been saved by the user. If only a reference branch was previously
  // saved we _don't_ show a new treatment branch by default and instead, if "handleAddBranch"
  // is called, we show the empty treatment branch instead of creating a new one.
  const [showFirstTreatmentBranch, setShowFirstTreatmentBranch] = useState(
    !defaultValues.referenceBranch?.slug ||
      (defaultValues.treatmentBranches &&
        defaultValues.treatmentBranches[0]?.slug),
  );

  const handleAddBranch = () => {
    commitFormData();
    if (
      showFirstTreatmentBranch ||
      (!showFirstTreatmentBranch && defaultValues.treatmentBranches === null)
    ) {
      dispatch({ type: "addBranch" });
    }
    if (!showFirstTreatmentBranch) setShowFirstTreatmentBranch(true);
  };

  const handleRemoveBranch = (idx: number) => () => {
    commitFormData();
    dispatch({ type: "removeBranch", idx });
  };

  const handleEqualRatioChange = (ev: React.ChangeEvent<HTMLInputElement>) => {
    commitFormData();
    dispatch({ type: "setEqualRatio", value: ev.target.checked });
  };

  const handleFeatureConfigChange = (
    value: getConfig_nimbusConfig_featureConfigs | null,
  ) => {
    commitFormData();
    dispatch({ type: "setFeatureConfig", value });
  };

  type DefaultValues = typeof defaultValues;
  const [handleSave, handleSaveNext] = [false, true].map((next) =>
    handleSubmit((dataIn: DefaultValues) => {
      try {
        commitFormData();
        onSave(
          extractSaveState(dataIn),
          setSubmitErrors,
          clearSubmitErrors,
          next,
        );
      } catch (error) {
        setSubmitErrors({ "*": [error.message] });
      }
    }),
  );

  const commonBranchProps = {
    equalRatio,
    featureConfigs,
    experimentFeatureConfig,
    onFeatureConfigChange: handleFeatureConfigChange,
    setSubmitErrors,
  };

  type FormBranchProps = React.ComponentProps<typeof FormBranch>;

  return (
    <FormProvider {...formMethods}>
      <Form
        data-testid="FormBranches"
        className="border-top my-3"
        noValidate
        onSubmit={handleSave}
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
                reviewErrors:
                  ({
                    ...fieldMessages.referenceBranch,
                    featureConfig: fieldMessages.featureConfig,
                  } as SerializerSet) || {},
                defaultValues: defaultValues.referenceBranch || {},
              }}
            />
          )}
          {treatmentBranches &&
            showFirstTreatmentBranch &&
            treatmentBranches.map((branch, idx) => {
              const treatmentBranchFieldMessages = (
                fieldMessages as SerializerMessages<SerializerSet[]>
              ).treatmentBranches?.[idx];

              return (
                <FormBranch
                  key={branch.key}
                  {...{
                    ...commonBranchProps,
                    fieldNamePrefix: `treatmentBranches[${idx}]`,
                    //@ts-ignore react-hook-form types seem broken for nested fields
                    errors: (errors?.treatmentBranches?.[idx] ||
                      {}) as FormBranchProps["errors"],
                    //@ts-ignore react-hook-form types seem broken for nested fields
                    touched: (touched?.treatmentBranches?.[idx] ||
                      {}) as FormBranchProps["touched"],
                    branch,
                    reviewErrors:
                      ({
                        ...treatmentBranchFieldMessages,
                        // Only show treatment branch feature config reviewErrors if the branch
                        // has been saved or if other fields have errors, otherwise a required
                        // feature config error can show on an optional branch
                        ...((treatmentBranches?.[idx].slug ||
                          treatmentBranchFieldMessages) && {
                          featureConfig: fieldMessages.featureConfig,
                        }),
                      } as SerializerSet) || {},
                    onRemove: handleRemoveBranch(idx),
                    defaultValues: defaultValues.treatmentBranches?.[idx] || {},
                  }}
                />
              );
            })}
        </section>

        <div className="d-flex flex-row-reverse bd-highlight">
          <div className="p-2">
            <button
              data-testid="next-button"
              className="btn btn-secondary"
              id="save-and-continue-button"
              disabled={isNextDisabled}
              onClick={handleSaveNext}
            >
              Save and Continue
            </button>
          </div>
          <div className="p-2">
            <button
              data-testid="save-button"
              type="submit"
              className="btn btn-primary"
              id="save-button"
              disabled={isSaveDisabled}
              onClick={handleSave}
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
