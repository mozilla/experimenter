/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_treatmentBranches,
} from "../../../../types/getExperiment";
import { TreatmentBranchType } from "../../../../types/globalTypes";

export type FormBranchesState = Pick<
  getExperiment_experimentBySlug,
  "featureConfig"
> & {
  referenceBranch: null | AnnotatedBranch;
  treatmentBranches: null | AnnotatedBranch[];
  equalRatio: boolean;
  lastId: number;
  globalErrors: string[];
};

export type AnnotatedBranch = TreatmentBranchType & {
  key: string;
  isValid: boolean;
  isDirty: boolean;
  errors: Record<string, string[]>;
};

export function createInitialState({
  featureConfig,
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
    featureConfig,
    globalErrors: [],
    referenceBranch: annotatedReferenceBranch,
    treatmentBranches: annotatedTreatmentBranches,
  };
}

export function annotateExperimentBranch(
  lastId: number | string,
  branch: getExperiment_experimentBySlug_treatmentBranches,
) {
  return {
    ...branch,
    key: `branch-${lastId}`,
    isValid: true,
    isDirty: false,
    errors: {},
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
