/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import Row from "react-bootstrap/Row";
import { FormProvider } from "react-hook-form";
import Select, {
  components as SelectComponents,
  MultiValueGenericProps,
  OptionProps,
  Options,
} from "react-select";
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
import {
  getConfig_nimbusConfig,
  getConfig_nimbusConfig_allFeatureConfigs,
} from "src/types/getConfig";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import { NimbusExperimentApplicationEnum } from "src/types/globalTypes";

interface FeatureConfigOption {
  value: string;
  name: string;
  description: string | null;
}

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
  const [selectDirty, setSelectDirty] = useState(false);

  let { fieldMessages, fieldWarnings } = useReviewCheck(experiment);

  [fieldMessages, fieldWarnings] = useMemo(() => {
    // When we change the selected features, the errors will not line up correctly.
    if (selectDirty) {
      return [{}, {}];
    }
    return [fieldMessages, fieldWarnings];
  }, [selectDirty, fieldMessages, fieldWarnings]);

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
      isLocalized,
      localizations,
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

  const onFeatureConfigsChanged = (newValue: Options<FeatureConfigOption>) => {
    setIsSelectValid(newValue.length > 0);
    setSelectDirty(true);

    return handleFeatureConfigsChange(
      newValue.map((value) => parseInt(value.value, 10)),
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

  const handleLocalizedChanged = (ev: React.ChangeEvent<HTMLInputElement>) => {
    commitFormData();
    dispatch({
      type: "setIsLocalized",
      value: ev.target.checked,
    });
  };

  const handleLocalizationsChanged = (ev: React.ChangeEvent) => {
    commitFormData();
    dispatch({
      type: "setLocalizations",
      value: (ev.target as HTMLTextAreaElement).value,
    });
  };

  type DefaultValues = typeof defaultValues;
  const [handleSave, handleSaveNext] = [false, true].map((next) =>
    handleSubmit((dataIn: DefaultValues) => {
      try {
        setIsFormSubmitted(true);
        setSelectDirty(false);
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

  const featureConfigOptions: FeatureConfigOption[] = useMemo(() => {
    return (allFeatureConfigs ?? [])
      .filter(
        (feature): feature is getConfig_nimbusConfig_allFeatureConfigs =>
          !!feature?.enabled,
      )
      .map((feature) => {
        return {
          name: feature.name,
          description: feature.description,
          value: feature.id!.toString(),
        };
      });
  }, [allFeatureConfigs]);

  const selectedFeatureConfigOptions: FeatureConfigOption[] = useMemo(
    () =>
      (experimentFeatureConfigIds ?? [])
        .filter<number>((id): id is number => typeof id !== "undefined")
        .map(
          (id) =>
            featureConfigOptions.find(
              (feature) => feature.value === id.toString(),
            )!,
        ),
    [experimentFeatureConfigIds, featureConfigOptions],
  );

  const optionDisabled = useCallback(
    () => selectedFeatureConfigOptions.length >= 20,
    [selectedFeatureConfigOptions.length],
  );

  const selectIsWarning = !!(
    fieldMessages.feature_configs ??
    fieldWarnings.feature_configs ??
    []
  ).length;

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
          <Row className={selectIsWarning ? "is-warning" : ""}>
            <Col>
              <Select<FeatureConfigOption, true>
                isMulti
                placeholder="Features..."
                options={featureConfigOptions}
                onChange={onFeatureConfigsChanged}
                value={selectedFeatureConfigOptions}
                aria-label="Features"
                instanceId="feature-configs"
                classNames={{
                  control: () => classNames({ "is-valid": selectValid }),
                }}
                classNamePrefix="react-select"
                getOptionLabel={(option: FeatureConfigOption) =>
                  option.description
                    ? `${option.name} - ${option.description}`
                    : option.name
                }
                isOptionDisabled={optionDisabled}
                components={{
                  MultiValueLabel: FeatureConfigSelectLabel,
                  Option: FeatureConfigSelectOption,
                }}
              />
            </Col>
            <Col sm={1} className="align-self-center text-center text-nowrap">
              {selectedFeatureConfigOptions.length} / 20
            </Col>
          </Row>
          {fieldMessages.feature_configs?.length && (
            // @ts-ignore This component doesn't technically support type="warning", but
            // all it's doing is using the string in a class, so we can safely override.
            <Form.Control.Feedback type="warning" data-for="featureConfigs">
              {(fieldMessages.feature_configs as SerializerMessage).join(", ")}
            </Form.Control.Feedback>
          )}
          {fieldWarnings.feature_configs?.length && (
            // @ts-ignore This component doesn't technically support type="warning", but
            // all it's doing is using the string in a class, so we can safely override.
            <Form.Control.Feedback type="warning" data-for="featureConfigs">
              {(fieldWarnings.feature_configs as SerializerMessage).join(", ")}
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
        {experiment.application === NimbusExperimentApplicationEnum.DESKTOP && (
          <Form.Group id="localizaton" className="mt-3">
            <h2>Localization</h2>
            <Form.Group controlId="isLocalized">
              <Form.Check
                label="Is this a localized experiment?"
                type="checkbox"
                name="isLocalized"
                data-testid="isLocalized"
                checked={!!isLocalized}
                onChange={handleLocalizedChanged}
              />
            </Form.Group>
            {isLocalized && (
              <Form.Group controlId="localizations" className="mt-2">
                <Form.Label>Localization Substitutions</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={5}
                  placeholder="Localization substitutions object"
                  name="localizations"
                  onChange={handleLocalizationsChanged}
                  value={localizations ?? ""}
                  isValid={
                    checkValid &&
                    typeof fieldMessages.localizations === "undefined"
                  }
                  data-testid="localizations"
                  className={classNames({
                    "is-warning":
                      (fieldMessages.localizations?.length ?? false) ||
                      (fieldWarnings.localizations?.length ?? false),
                  })}
                />
                {fieldMessages.localizations?.length && (
                  <Form.Control.Feedback
                    // @ts-ignore This component doesn't technically support type="warning", but
                    // all it's doing is using the string in a class, so we can safely override.
                    type="warning"
                    data-for="localizations"
                  >
                    {(fieldMessages.localizations as SerializerMessage).join(
                      ", ",
                    )}
                  </Form.Control.Feedback>
                )}
                {fieldWarnings.localizations?.length && (
                  <Form.Control.Feedback
                    // @ts-ignore This component doesn't technically support type="warning", but
                    // all it's doing is using the string in a class, so we can safely override.
                    type="warning"
                    data-for="localizations"
                  >
                    {(fieldWarnings.localizations as SerializerMessage).join(
                      ", ",
                    )}
                  </Form.Control.Feedback>
                )}
              </Form.Group>
            )}
          </Form.Group>
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

function FeatureConfigSelectLabel(
  props: MultiValueGenericProps<FeatureConfigOption>,
) {
  return (
    <SelectComponents.MultiValueLabel {...props}>
      {props.data.name}
    </SelectComponents.MultiValueLabel>
  );
}

function FeatureConfigSelectOption(
  props: OptionProps<FeatureConfigOption, true>,
) {
  return (
    // @ts-ignore innerProps are passed directly to the underlying <div> and
    // data-* attributes are valid, but they do not appear in the prop types.
    <SelectComponents.Option
      {...{
        ...props,
        innerProps: {
          ...props.innerProps,
          "data-feature-config-id": props.data.value,
        },
      }}
    />
  );
}

export default FormBranches;
