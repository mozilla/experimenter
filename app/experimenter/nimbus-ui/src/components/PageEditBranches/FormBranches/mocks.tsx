/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect } from "react";
import { FormProvider } from "react-hook-form";
import FormBranches from ".";
import { useForm } from "../../../hooks";
import { mockExperimentQuery, MOCK_CONFIG } from "../../../lib/mocks";
import { BranchInput } from "../../../types/globalTypes";
import FormBranch from "./FormBranch";
import { AnnotatedBranch } from "./reducer";
import { formBranchesActionReducer } from "./reducer/actions";
import { FormBranchesState } from "./reducer/state";

export const MOCK_EXPERIMENT = mockExperimentQuery("demo-slug", {
  referenceBranch: {
    id: 123,
    name: "User-centric mobile solution",
    slug: "control",
    description: "Behind almost radio result personal none future current.",
    ratio: 1,
    featureValues: [
      {
        featureConfig: null,
        enabled: true,
        value: '{"environmental-fact": "really-citizen"}',
      },
    ],
    screenshots: [],
  },
  treatmentBranches: [
    {
      id: 456,
      name: "Managed zero tolerance projection",
      slug: "managed-zero-tolerance-projection",
      description: "Next ask then he in degree order.",
      ratio: 1,
      featureValues: [
        {
          featureConfig: null,
          enabled: false,
          value: '{"effect-effect-whole": "close-teach-exactly"}',
        },
      ],
      screenshots: [],
    },
    {
      id: 789,
      name: "Salt way link",
      slug: "salt-way-link",
      description: "Flame the dark true.",
      ratio: 2,
      featureValues: [
        {
          featureConfig: null,
          enabled: true,
          value: '{"frosted-wake": "simple-hesitation"}',
        },
      ],
      screenshots: [],
    },
  ],
}).experiment;

const MOCK_STATE: FormBranchesState = {
  equalRatio: true,
  lastId: 0,
  globalErrors: [],
  featureConfigs: MOCK_EXPERIMENT.featureConfigs!.map((f) => f.id),
  referenceBranch: {
    ...MOCK_EXPERIMENT.referenceBranch!,
    featureValues: MOCK_EXPERIMENT.referenceBranch!.featureValues!.map(
      (fv) => ({
        ...fv,
        featureConfig: fv!.featureConfig!.id,
      }),
    ),
    screenshots: [],
    key: "branch-reference",
    errors: {},
    isValid: true,
    isDirty: false,
  },
  treatmentBranches: MOCK_EXPERIMENT.treatmentBranches!.map((branch, idx) => ({
    ...branch!,
    featureValues: branch!.featureValues!.map((fv) => ({
      ...fv,
      featureConfig: fv!.featureConfig!.id,
    })),
    screenshots: [],
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
  onAddScreenshot = () => {},
  onRemoveScreenshot = () => {},
  onRemove = () => {},
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
            onRemove,
            onAddScreenshot,
            onRemoveScreenshot,
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
  allFeatureConfigs = MOCK_CONFIG.featureConfigs,
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
          allFeatureConfigs,
          onSave,
        }}
      />
    </div>
  );
};

export const MOCK_BRANCH: BranchInput = {
  ...MOCK_EXPERIMENT.treatmentBranches![0]!,
  featureValues: MOCK_EXPERIMENT.treatmentBranches![0]!.featureValues?.map(
    (fv) => ({ ...fv, featureConfig: fv.featureConfig?.id }),
  ),
};
export const MOCK_ANNOTATED_BRANCH: AnnotatedBranch = {
  ...MOCK_BRANCH,
  key: "branch-1",
  isValid: true,
  isDirty: false,
  errors: {},
  screenshots: [],
};
export const MOCK_FEATURE_CONFIG = MOCK_CONFIG.featureConfigs![0]!;
export const MOCK_FEATURE_CONFIG_WITH_SCHEMA = MOCK_CONFIG.featureConfigs![1]!;
