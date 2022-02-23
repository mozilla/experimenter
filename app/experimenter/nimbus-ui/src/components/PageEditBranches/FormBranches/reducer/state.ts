/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_treatmentBranches,
} from "../../../../types/getExperiment";
import {
  ExperimentInput,
  TreatmentBranchInput,
} from "../../../../types/globalTypes";

export type FormBranchesState = Pick<
  ExperimentInput,
  "featureConfigIds" | "warnFeatureSchema"
> & {
  referenceBranch: null | AnnotatedBranch;
  treatmentBranches: null | AnnotatedBranch[];
  equalRatio: boolean;
  lastId: number;
  globalErrors: string[];
};

export type AnnotatedBranch = Omit<TreatmentBranchInput, "id"> & {
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
  warnFeatureSchema,
  referenceBranch,
  treatmentBranches,
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
    globalErrors: [],
    referenceBranch: annotatedReferenceBranch,
    treatmentBranches: annotatedTreatmentBranches,
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
  };
}

export function createAnnotatedBranch(
  lastId: number,
  name: string,
): AnnotatedBranch {
  return {
    key: `branch-${lastId}`,
    errors: {},
    isValid: false,
    isDirty: false,
    name,
    description: "",
    ratio: 1,
    featureValue: null,
    featureEnabled: false,
  };
}
