/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React, { useEffect, useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import { FormProvider } from "react-hook-form";
import FormBranch from "src/components/PageEditBranches/FormBranches/FormBranch";
import {
  FormBranchesSaveState,
  REFERENCE_BRANCH_IDX,
  useFormBranchesReducer,
} from "src/components/PageEditBranches/FormBranches/reducer";
import { FormBranchesState } from "src/components/PageEditBranches/FormBranches/reducer/state";
import { FormData } from "src/components/PageEditBranches/FormBranches/reducer/update";
import { useExitWarning, useForm, useReviewCheck } from "src/hooks";
import { IsDirtyUnsaved } from "src/hooks/useCommonForm/useCommonFormMethods";
import { getConfig_nimbusConfig } from "src/types/getConfig";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import { NimbusExperimentApplicationEnum } from "src/types/globalTypes";

type FormBranchesProps = {
  isLoading: boolean;
  experiment: getExperiment_experimentBySlug;
  allFeatureConfigs: getConfig_nimbusConfig["allFeatureConfigs"];
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
  allFeatureConfigs,
  onSave,
}: FormBranchesProps) => {
  const { fieldMessages, fieldWarnings } = useReviewCheck(experiment);

  const [
    {
      featureConfigIds: experimentFeatureConfigIds,
      warnFeatureSchema,
      isRollout,
      referenceBranch,
      treatmentBranches,
      equalRatio,
      preventPrefConflicts,
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

  const doFeaturesSetPrefs = (featureConfigIds: (number | null)[]) => {
    return featureConfigIds.some(
      (id) =>
        (id !== null &&
          allFeatureConfigs?.find((config) => config?.id === id)?.setsPrefs) ??
        false,
    );
  };

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
  const [formSubmitted, setIsFormSubmitted] = useState(false);
  const [selectValid, setIsSelectValid] = useState(false);
  const [checkValid, setIsCheckValid] = useState(false);

  const shouldWarnOnExit = useExitWarning();
  useEffect(() => {
    shouldWarnOnExit(isDirtyUnsaved);
    setIsFormSubmitted(false);
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
    if (!isRollout) {
      commitFormData();
      dispatch({ type: "addBranch" });
    }
  };

  const handleRemoveBranch = (idx: number) => () => {
    commitFormData();
    dispatch({ type: "removeBranch", idx });
  };

  const handleEqualRatioChange = (ev: React.ChangeEvent<HTMLInputElement>) => {
    setIsCheckValid(true);
    commitFormData();
    dispatch({ type: "setEqualRatio", value: ev.target.checked });
  };

  const handlePreventPrefConflictsChange = (
    ev: React.ChangeEvent<HTMLInputElement>,
  ) => {
    commitFormData();
    dispatch({
      type: "setPreventPrefConflicts",
      preventPrefConflicts: ev.target.checked,
    });
  };

  const handlewarnFeatureSchema = (ev: React.ChangeEvent<HTMLInputElement>) => {
    setIsCheckValid(true);
    commitFormData();
    dispatch({
      type: "setwarnFeatureSchema",
      value: ev.target.checked,
    });
  };

  const handleFeatureConfigsChange = (
    value: FormBranchesState["featureConfigIds"],
  ) => {
    commitFormData();
    dispatch({ type: "setFeatureConfigs", value });

    if (value && doFeaturesSetPrefs(value) && preventPrefConflicts) {
      dispatch({
        type: "setPreventPrefConflicts",
        preventPrefConflicts: false,
      });
    }
  };

  const handleIsRollout = (ev: React.ChangeEvent<HTMLInputElement>) => {
    setIsCheckValid(true);
    commitFormData();
    dispatch({
      type: "setIsRollout",
      value: ev.target.checked,
    });
  };

  const onFeatureConfigChange = (ev: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFeatureId = parseInt(ev.target.value, 10);
    setIsSelectValid(true);
    return handleFeatureConfigsChange(
      isNaN(selectedFeatureId) ? [] : [selectedFeatureId],
    );
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
        setIsFormSubmitted(true);
        if (!isLoading) {
          commitFormData();
          onSave(
            extractSaveState(dataIn),
            setSubmitErrors,
            clearSubmitErrors,
            next,
          );
        }
      } catch (error: any) {
        setSubmitErrors({ "*": [error.message] });
      }
    }),
  );

  const commonBranchProps = {
    equalRatio,
    setSubmitErrors,
  };

  type FormBranchProps = React.ComponentProps<typeof FormBranch>;

  const isDesktop =
    experiment.application === NimbusExperimentApplicationEnum.DESKTOP;

  const featureSetsPrefs =
    experimentFeatureConfigIds &&
    doFeaturesSetPrefs(experimentFeatureConfigIds);

  const isArchived =
    experiment?.isArchived != null ? experiment.isArchived : false;

  return (
    <FormProvider {...formMethods}>
      <Form
        data-testid="FormBranches"
        className="my-3"
        noValidate
        onSubmit={handleSave}
        validated={isValid && formSubmitted}
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
            isValid={selectValid}
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
            custom
            onChange={onFeatureConfigChange}
            value={
              experimentFeatureConfigIds?.length
                ? experimentFeatureConfigIds[0] || undefined
                : undefined
            }
          >
            <option value="">Select...</option>
            {allFeatureConfigs
              ?.filter((feature) => feature?.enabled)
              .map((feature) => (
                <option
                  key={`feature-${feature?.slug}-${feature?.id!}`}
                  value={feature?.id!}
                >
                  {feature?.name}
                  {feature?.description?.length
                    ? ` - ${feature.description}`
                    : ""}
                </option>
              ))}
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
              isValid={!!isRollout && checkValid}
              data-testid="is-rollout-checkbox"
              onChange={handleIsRollout}
              checked={!!isRollout}
              type="checkbox"
              isInvalid={!!fieldMessages?.is_rollout}
              feedback={fieldMessages?.is_rollout}
              label={
                <>
                  This is a rollout (single branch).{" "}
                  <a
                    href="https://experimenter.info/deep-dives/experimenter/rollouts"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Learn more
                  </a>
                </>
              }
            />
          </Form.Group>
        </Form.Row>

        <Form.Row>
          <Form.Group as={Col} controlId="warnFeatureSchema">
            <Form.Check
              isValid={!!warnFeatureSchema && checkValid}
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
              isValid={equalRatio && checkValid}
              data-testid="equal-ratio-checkbox"
              onChange={handleEqualRatioChange}
              checked={equalRatio}
              type="checkbox"
              label="Users should be split evenly between all branches"
            />
          </Form.Group>
        </Form.Row>

        {featureSetsPrefs && (
          <Form.Row>
            <Form.Group as={Col} controlId="preventPrefConflicts">
              <Form.Check
                data-testid="prevent-pref-conflicts-checkbox"
                label="Prevent enrollment if users have changed any prefs set by this experiment"
                onChange={handlePreventPrefConflictsChange}
                checked={preventPrefConflicts}
              />
            </Form.Group>
          </Form.Row>
        )}

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
                isDesktop,
              }}
            />
          )}
          {treatmentBranches &&
            !isRollout &&
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
                    isDesktop,
                  }}
                />
              );
            })}
        </section>
        {!isRollout && (
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
              disabled={isNextDisabled || isArchived}
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
              disabled={isSaveDisabled || isArchived}
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
