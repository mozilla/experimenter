/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect } from "react";
import { useForm, FormProvider } from "react-hook-form";
import FormBranches from ".";
import FormBranch from "./FormBranch";
import { mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";
import { AnnotatedBranch } from "./reducer";

type FormBranchProps = React.ComponentProps<typeof FormBranch>;

export const SubjectBranch = ({
  fieldNamePrefix = "referenceBranch",
  branch = MOCK_ANNOTATED_BRANCH,
  reviewErrors,
  equalRatio = false,
  isReference = false,
  experimentFeatureConfig = MOCK_FEATURE_CONFIG,
  featureConfig = MOCK_CONFIG.featureConfig,
  onRemove = () => {},
  onAddFeatureConfig = () => {},
  onRemoveFeatureConfig = () => {},
  onFeatureConfigChange = () => {},
}: Partial<React.ComponentProps<typeof FormBranch>>) => {
  const defaultValues = {
    referenceBranch: branch,
    treatmentBranches: [branch],
  };

  const formMethods = useForm({
    mode: "onBlur",
    defaultValues,
  });

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
            reviewErrors,
            branch,
            isReference,
            equalRatio,
            featureConfig,
            experimentFeatureConfig,
            onRemove,
            onAddFeatureConfig,
            onRemoveFeatureConfig,
            onFeatureConfigChange,
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
  onNext = () => {},
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
          onNext,
        }}
      />
    </div>
  );
};

export const MOCK_EXPERIMENT = mockExperimentQuery("demo-slug", {
  treatmentBranches: [
    {
      __typename: "NimbusBranchType",
      name: "Managed zero tolerance projection",
      slug: "managed-zero-tolerance-projection",
      description: "Next ask then he in degree order.",
      ratio: 1,
      featureValue: '{"effect-effect-whole": "close-teach-exactly"}',
      featureEnabled: false,
    },
    {
      __typename: "NimbusBranchType",
      name: "Salt way link",
      slug: "salt-way-link",
      description: "Flame the dark true.",
      ratio: 2,
      featureValue: '{"frosted-wake": "simple-hesitation"}',
      featureEnabled: true,
    },
  ],
}).experiment;

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
