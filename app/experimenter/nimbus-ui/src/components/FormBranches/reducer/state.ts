/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_treatmentBranches,
} from "../../../types/getExperiment";

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

export type AnnotatedBranch = getExperiment_experimentBySlug_treatmentBranches & {
  key: string;
  isValid: boolean;
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
      : annotateBranch("reference", referenceBranch!);

  const annotatedTreatmentBranches = !Array.isArray(treatmentBranches)
    ? null
    : treatmentBranches.map((branch) => annotateBranch(lastId++, branch!));

  return {
    lastId,
    equalRatio,
    featureConfig,
    globalErrors: [],
    referenceBranch: annotatedReferenceBranch,
    treatmentBranches: annotatedTreatmentBranches,
  };
}

export function annotateBranch(
  lastId: number | string,
  branch: getExperiment_experimentBySlug_treatmentBranches,
) {
  return {
    ...branch,
    key: `branch-${lastId}`,
    isValid: true,
    errors: {},
  };
}

export function createBranch(lastId: number, name: string): AnnotatedBranch {
  return {
    __typename: "NimbusBranchType" as const,
    key: `branch-${lastId}`,
    errors: {},
    isValid: false,
    name,
    slug: "",
    description: "",
    ratio: 1,
    featureValue: null,
    featureEnabled: true,
  };
}
