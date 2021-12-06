/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React, { useEffect, useMemo } from "react";
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
import {
  FormBranchesSaveState,
  REFERENCE_BRANCH_IDX,
  useFormBranchesReducer,
} from "./reducer";
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
  const { fieldMessages, fieldWarnings } = useReviewCheck(experiment);

  const [
    {
      featureConfig: experimentFeatureConfig,
      warnFeatureSchema,
      isRollout,
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

  const handlewarnFeatureSchema = (ev: React.ChangeEvent<HTMLInputElement>) => {
    commitFormData();
    dispatch({
      type: "setwarnFeatureSchema",
      value: ev.target.checked,
    });
  };

  const handleIsRollout = (ev: React.ChangeEvent<HTMLInputElement>) => {
    commitFormData();
    dispatch({
      type: "setIsRollout",
      value: ev.target.checked,
    });
  };

  const handleFeatureConfigChange = (
    value: getConfig_nimbusConfig_featureConfigs | null,
  ) => {
    commitFormData();
    dispatch({ type: "setFeatureConfig", value });
  };

  const onFeatureConfigChange = (ev: React.ChangeEvent<HTMLInputElement>) => {
    const selectedIdx = parseInt(ev.target.value, 10);
    if (isNaN(selectedIdx)) {
      return handleFeatureConfigChange(null);
    }
    // featureConfig shouldn't ever be null in practice
    const feature = featureConfigs![selectedIdx];
    return handleFeatureConfigChange(feature);
  };

  const handleAddScreenshot = (branchIdx: number) => () => {
    commitFormData();
    dispatch({ type: "addScreenshotToBranch", branchIdx });
  };

  const handleRemoveScreenshot =
    (branchIdx: number) => (screenshotIdx: number) => {
      commitFormData();
      dispatch({
        type: "removeScreenshotFromBranch",
        branchIdx,
        screenshotIdx,
      });
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
      } catch (error: any) {
        setSubmitErrors({ "*": [error.message] });
      }
    }),
  );

  const commonBranchProps = {
    equalRatio,
    experimentFeatureConfig,
    setSubmitErrors,
  };

  type FormBranchProps = React.ComponentProps<typeof FormBranch>;

  return (
    <FormProvider {...formMethods}>
      <Form
        data-testid="FormBranches"
        className="my-3"
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

        <Form.Group>
          <Form.Control
            as="select"
            name="featureConfig"
            data-testid="feature-config-select"
            // Displaying the review-readiness error is handled here instead of `formControlAttrs`
            // due to a state conflict between `react-hook-form` and our internal branch state mangement
            className={classNames({
              "is-warning":
                fieldMessages.feature_config?.length > 0 ||
                fieldWarnings.feature_config?.length > 0,
            })}
            onChange={onFeatureConfigChange}
            value={featureConfigs!.findIndex(
              (feature) => feature?.slug === experimentFeatureConfig?.slug,
            )}
          >
            <option value="">Select...</option>
            {featureConfigs?.map(
              (feature, idx) =>
                feature && (
                  <option key={`feature-${feature.slug}-${idx}`} value={idx}>
                    {feature.name}
                  </option>
                ),
            )}
          </Form.Control>
          {fieldMessages.feature_config?.length > 0 && (
            // @ts-ignore This component doesn't technically support type="warning", but
            // all it's doing is using the string in a class, so we can safely override.
            <Form.Control.Feedback type="warning" data-for="featureConfig">
              {(fieldMessages.feature_config as SerializerMessage).join(", ")}
            </Form.Control.Feedback>
          )}
          {fieldWarnings.feature_config?.length > 0 && (
            // @ts-ignore This component doesn't technically support type="warning", but
            // all it's doing is using the string in a class, so we can safely override.
            <Form.Control.Feedback type="warning" data-for="featureConfig">
              {(fieldWarnings.feature_config as SerializerMessage).join(", ")}
            </Form.Control.Feedback>
          )}
        </Form.Group>

        <Form.Row>
          <Form.Group as={Col} controlId="isRollout">
            <Form.Check
              data-testid="is-rollout-checkbox"
              onChange={handleIsRollout}
              checked={!!isRollout}
              type="checkbox"
              label="Handle this experiment as a single-branch rollout"
            />
          </Form.Group>
        </Form.Row>

        <Form.Row>
          <Form.Group as={Col} controlId="warnFeatureSchema">
            <Form.Check
              data-testid="equal-warn-on-feature-value-schema-invalid-checkbox"
              onChange={handlewarnFeatureSchema}
              checked={!!warnFeatureSchema}
              type="checkbox"
              label="Warn only on feature schema validation failure"
            />
          </Form.Group>
        </Form.Row>

        <Form.Row>
          <Form.Group as={Col} controlId="evenRatio">
            <Form.Check
              data-testid="equal-ratio-checkbox"
              onChange={handleEqualRatioChange}
              checked={equalRatio}
              type="checkbox"
              label="Users should be split evenly between all branches"
            />
          </Form.Group>
        </Form.Row>

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
                reviewErrors: fieldMessages.reference_branch as SerializerSet,
                reviewWarnings: fieldWarnings.reference_branch as SerializerSet,
                onAddScreenshot: handleAddScreenshot(REFERENCE_BRANCH_IDX),
                onRemoveScreenshot:
                  handleRemoveScreenshot(REFERENCE_BRANCH_IDX),
                defaultValues: defaultValues.referenceBranch || {},
              }}
            />
          )}
          {treatmentBranches &&
            treatmentBranches.map((branch, idx) => {
              const reviewErrors = (
                fieldMessages as SerializerMessages<SerializerSet[]>
              ).treatment_branches?.[idx];
              const reviewWarnings = (
                fieldWarnings as SerializerMessages<SerializerSet[]>
              ).treatment_branches?.[idx];

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
                    reviewErrors,
                    reviewWarnings,
                    onRemove: handleRemoveBranch(idx),
                    onAddScreenshot: handleAddScreenshot(idx),
                    onRemoveScreenshot: handleRemoveScreenshot(idx),
                    defaultValues: defaultValues.treatmentBranches?.[idx] || {},
                  }}
                />
              );
            })}
        </section>
        {!experiment.isRollout && (
          <Button
            data-testid="add-branch"
            variant="outline-primary"
            size="sm"
            onClick={handleAddBranch}
          >
            + Add branch
          </Button>
        )}
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
