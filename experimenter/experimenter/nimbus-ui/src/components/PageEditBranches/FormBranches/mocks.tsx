/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect } from "react";
import { FormProvider } from "react-hook-form";
import FormBranches from "src/components/PageEditBranches/FormBranches";
import FormBranch from "src/components/PageEditBranches/FormBranches/FormBranch";
import { AnnotatedBranch } from "src/components/PageEditBranches/FormBranches/reducer";
import { formBranchesActionReducer } from "src/components/PageEditBranches/FormBranches/reducer/actions";
import { FormBranchesState } from "src/components/PageEditBranches/FormBranches/reducer/state";
import { useForm } from "src/hooks";
import { MockedCache, mockExperimentQuery, MOCK_CONFIG } from "src/lib/mocks";
import { NimbusExperimentApplicationEnum } from "src/types/globalTypes";

export const MOCK_EXPERIMENT = mockExperimentQuery("demo-slug", {
  application: NimbusExperimentApplicationEnum.DESKTOP,
  featureConfigs: [], //MOCK_CONFIG!.featureConfigs![0],
  isRollout: false,
  warnFeatureSchema: false,
  referenceBranch: {
    id: 123,
    name: "User-centric mobile solution",
    slug: "control",
    description: "Behind almost radio result personal none future current.",
    ratio: 1,
    featureValues: [
      {
        featureConfig: { id: 1 },
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
          featureConfig: { id: 1 },
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
          featureConfig: { id: 1 },
          value: '{"frosted-wake": "simple-hesitation"}',
        },
      ],
      screenshots: [],
    },
  ],
}).experiment;

const MOCK_STATE: FormBranchesState = {
  equalRatio: true,
  preventPrefConflicts: false,
  lastId: 0,
  globalErrors: [],
  featureConfigIds: [],
  warnFeatureSchema: false,
  isRollout: false,
  referenceBranch: {
    ...MOCK_EXPERIMENT.referenceBranch!,
    screenshots: [],
    key: "branch-reference",
    errors: {},
    isValid: true,
    isDirty: false,
    featureValues: MOCK_EXPERIMENT.referenceBranch?.featureValues?.map(
      (fv) => ({
        featureConfig: fv?.featureConfig?.id?.toString(),
        value: fv?.value,
      }),
    ),
  },
  treatmentBranches: MOCK_EXPERIMENT.treatmentBranches!.map((branch, idx) => ({
    ...branch!,
    screenshots: [],
    key: `branch-${idx}`,
    errors: {},
    isValid: true,
    isDirty: false,
    featureValues: branch?.featureValues?.map((fv) => ({
      featureConfig: fv?.featureConfig?.id?.toString(),
      value: fv?.value,
    })),
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
  isDesktop = true,
  config = MOCK_CONFIG,
}: Partial<React.ComponentProps<typeof FormBranch>> & {
  config?: typeof MOCK_CONFIG;
}) => {
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
    <MockedCache config={config}>
      <FormProvider {...formMethods}>
        <form className="p-5">
          <FormBranch
            {...{
              fieldNamePrefix,
              // react-hook-form types seem broken for nested fields
              errors: (errors.referenceBranch ||
                {}) as FormBranchProps["errors"],
              // react-hook-form types seem broken for nested fields
              touched: (touched.referenceBranch ||
                {}) as FormBranchProps["touched"],
              reviewErrors: {},
              reviewWarnings: {},
              branch,
              isReference,
              equalRatio,
              onRemove,
              onAddScreenshot,
              onRemoveScreenshot,
              defaultValues: defaultValues.referenceBranch || {},
              setSubmitErrors,
              isDesktop,
            }}
          />
        </form>
      </FormProvider>
    </MockedCache>
  );
};

export const SubjectBranches = ({
  isLoading = false,
  experiment = MOCK_EXPERIMENT,
  allFeatureConfigs = MOCK_CONFIG.allFeatureConfigs,
  onSave = () => {},
  saveOnInitialRender = false,
  config = MOCK_CONFIG,
}: Partial<React.ComponentProps<typeof FormBranches>> & {
  saveOnInitialRender?: boolean;
  config?: typeof MOCK_CONFIG;
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
    <MockedCache config={config}>
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
    </MockedCache>
  );
};

export const MOCK_BRANCH = MOCK_EXPERIMENT.treatmentBranches![0]!;
export const MOCK_ANNOTATED_BRANCH: AnnotatedBranch = {
  key: "branch-1",
  isValid: true,
  isDirty: false,
  errors: {},
  ...MOCK_BRANCH,
  screenshots: [],
  featureValues: MOCK_BRANCH.featureValues?.map((fv) => ({
    featureConfig: fv?.featureConfig?.id?.toString(),
    value: fv?.value,
  })),
};
export const MOCK_FEATURE_CONFIG = MOCK_CONFIG.allFeatureConfigs![0]!;
export const MOCK_FEATURE_CONFIG_WITH_SCHEMA =
  MOCK_CONFIG.allFeatureConfigs![1]!;
export const MOCK_FEATURE_CONFIG_WITH_SETS_PREFS =
  MOCK_CONFIG.allFeatureConfigs![4]!;
