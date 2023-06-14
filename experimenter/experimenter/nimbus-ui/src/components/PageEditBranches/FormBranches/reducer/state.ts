/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_treatmentBranches,
} from "src/types/getExperiment";
import { BranchInput, ExperimentInput } from "src/types/globalTypes";

export type FormBranchesState = Pick<
  ExperimentInput,
  | "featureConfigIds"
  | "warnFeatureSchema"
  | "isRollout"
  | "isLocalized"
  | "localizations"
> & {
  referenceBranch: null | AnnotatedBranch;
  treatmentBranches: null | AnnotatedBranch[];
  equalRatio: boolean;
  preventPrefConflicts: boolean;
  lastId: number;
  globalErrors: string[];
};

export type AnnotatedBranch = Omit<BranchInput, "id"> & {
  id?: number | null;
  key: string;
  isValid: boolean;
  isDirty: boolean;
  errors: SerializerSet;
  slug?: string;
  reviewMessages?: Record<string, any>;
};

export function createInitialState({
  featureConfigs,
  preventPrefConflicts,
  warnFeatureSchema,
  isRollout,
  referenceBranch,
  treatmentBranches,
  isLocalized,
  localizations,
}: getExperiment_experimentBySlug): FormBranchesState {
  let lastId = 0;

  const equalRatio =
    treatmentBranches !== null &&
    treatmentBranches?.every(
      (branch) => branch?.ratio === referenceBranch?.ratio,
    );

  const annotatedReferenceBranch =
    referenceBranch === null
      ? null
      : annotateExperimentBranch("reference", referenceBranch!);

  const annotatedTreatmentBranches = !Array.isArray(treatmentBranches)
    ? null
    : treatmentBranches.map((branch) =>
        annotateExperimentBranch(lastId++, branch!),
      );

  return {
    lastId,
    equalRatio,
    featureConfigIds: featureConfigs?.map((f) => f?.id || null),
    warnFeatureSchema,
    isRollout,
    globalErrors: [],
    referenceBranch: annotatedReferenceBranch,
    treatmentBranches: annotatedTreatmentBranches,
    preventPrefConflicts: preventPrefConflicts ?? false,
    isLocalized,
    localizations,
  };
}

export function annotateExperimentBranch(
  lastId: number | string,
  branch: getExperiment_experimentBySlug_treatmentBranches,
): AnnotatedBranch {
  return {
    ...branch,
    key: `branch-${lastId}`,
    isValid: true,
    isDirty: false,
    errors: {},
    reviewMessages: {},
    featureValues: branch.featureValues?.map((fv) => ({
      featureConfig: fv?.featureConfig?.id?.toString(),
      value: fv?.value,
    })),
  };
}

export function createAnnotatedBranch(
  lastId: number,
  name: string,
  featureConfigIds: FormBranchesState["featureConfigIds"],
): AnnotatedBranch {
  return {
    key: `branch-${lastId}`,
    errors: {},
    isValid: false,
    isDirty: false,
    name,
    description: "",
    ratio: 1,
    featureValues: featureConfigIds?.map((featureConfigId) => ({
      featureConfig: featureConfigId?.toString(),
      value: "",
    })),
  };
}
