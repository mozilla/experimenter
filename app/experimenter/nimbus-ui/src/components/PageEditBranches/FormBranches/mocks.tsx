/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect } from "react";
import { FormProvider } from "react-hook-form";
import FormBranches from ".";
import { useForm } from "../../../hooks";
import { mockExperimentQuery, MOCK_CONFIG } from "../../../lib/mocks";
import FormBranch from "./FormBranch";
import { AnnotatedBranch } from "./reducer";
import { formBranchesActionReducer } from "./reducer/actions";
import { FormBranchesState } from "./reducer/state";

export const MOCK_EXPERIMENT = mockExperimentQuery("demo-slug", {
  treatmentBranches: [
    {
      name: "Managed zero tolerance projection",
      slug: "managed-zero-tolerance-projection",
      description: "Next ask then he in degree order.",
      ratio: 1,
      featureValue: '{"effect-effect-whole": "close-teach-exactly"}',
      featureEnabled: false,
    },
    {
      name: "Salt way link",
      slug: "salt-way-link",
      description: "Flame the dark true.",
      ratio: 2,
      featureValue: '{"frosted-wake": "simple-hesitation"}',
      featureEnabled: true,
    },
  ],
}).experiment;

const MOCK_STATE: FormBranchesState = {
  equalRatio: true,
  lastId: 0,
  globalErrors: [],
  featureConfig: MOCK_EXPERIMENT.featureConfig,
  referenceBranch: {
    ...MOCK_EXPERIMENT.referenceBranch!,
    key: "branch-reference",
    errors: {},
    isValid: true,
    isDirty: false,
  },
  treatmentBranches: MOCK_EXPERIMENT.treatmentBranches!.map((branch, idx) => ({
    ...branch!,
    key: `branch-${idx}`,
    errors: {},
    isValid: true,
    isDirty: false,
  })),
};

type FormBranchProps = React.ComponentProps<typeof FormBranch>;

export const SubjectBranch = ({
  fieldNamePrefix = "referenceBranch",
  branch = MOCK_ANNOTATED_BRANCH,
  equalRatio = false,
  isReference = false,
  experimentFeatureConfig = MOCK_FEATURE_CONFIG,
  featureConfig = MOCK_CONFIG.featureConfig,
  onRemove = () => {},
  onFeatureConfigChange = () => {},
}: Partial<React.ComponentProps<typeof FormBranch>>) => {
  const defaultValues = {
    referenceBranch: branch,
    treatmentBranches: [branch],
  };
  // TODO: EXP-614 submitErrors type is any, but in practical use it's AnnotatedBranch["errors"]
  const setSubmitErrors = (submitErrors: any) =>
    formBranchesActionReducer(MOCK_STATE, {
      type: "setSubmitErrors",
      submitErrors,
    });

  const formMethods = useForm(defaultValues);

  const {
    formState: { errors, touched },
  } = formMethods;

  return (
    <FormProvider {...formMethods}>
      <form className="p-5">
        <FormBranch
          {...{
            fieldNamePrefix,
            // react-hook-form types seem broken for nested fields
            errors: (errors.referenceBranch || {}) as FormBranchProps["errors"],
            // react-hook-form types seem broken for nested fields
            touched: (touched.referenceBranch ||
              {}) as FormBranchProps["touched"],
            reviewErrors: {},
            branch,
            isReference,
            equalRatio,
            featureConfig,
            experimentFeatureConfig,
            onRemove,
            onFeatureConfigChange,
            defaultValues: defaultValues.referenceBranch || {},
            setSubmitErrors,
          }}
        />
      </form>
    </FormProvider>
  );
};

export const SubjectBranches = ({
  isLoading = false,
  experiment = MOCK_EXPERIMENT,
  featureConfig = MOCK_CONFIG.featureConfig,
  onSave = () => {},
  saveOnInitialRender = false,
}: Partial<React.ComponentProps<typeof FormBranches>> & {
  saveOnInitialRender?: boolean;
} = {}) => {
  useEffect(() => {
    if (saveOnInitialRender) {
      // HACK: this is dirty but it works
      const saveButton = document!.querySelector(
        "button[data-testid=save-button]",
      )! as HTMLInputElement;
      saveButton.click();
    }
  }, [saveOnInitialRender]);

  return (
    <div className="p-5">
      <FormBranches
        {...{
          isLoading,
          experiment,
          featureConfig,
          onSave,
        }}
      />
    </div>
  );
};

export const MOCK_BRANCH = MOCK_EXPERIMENT.treatmentBranches![0]!;
export const MOCK_ANNOTATED_BRANCH: AnnotatedBranch = {
  key: "branch-1",
  isValid: true,
  isDirty: false,
  errors: {},
  ...MOCK_BRANCH,
};
export const MOCK_FEATURE_CONFIG = MOCK_CONFIG.featureConfig![0]!;
export const MOCK_FEATURE_CONFIG_WITH_SCHEMA = MOCK_CONFIG.featureConfig![1]!;
