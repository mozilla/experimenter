/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  AnnotatedBranch,
  FormBranchesState,
} from "src/components/PageEditBranches/FormBranches/reducer/state";
import { CONTROL_BRANCH_REQUIRED_ERROR } from "src/lib/constants";
import {
  BranchFeatureValueInput,
  BranchScreenshotInput,
  ExperimentInput,
} from "src/types/globalTypes";

export type FormBranchesSaveState = Pick<
  ExperimentInput,
  | "featureConfigIds"
  | "warnFeatureSchema"
  | "isRollout"
  | "referenceBranch"
  | "treatmentBranches"
  | "preventPrefConflicts"
  | "isLocalized"
  | "localizations"
>;

export class UpdateStateError extends Error {}

export type FormData = {
  referenceBranch: Partial<AnnotatedBranch> | null;
  treatmentBranches: Partial<AnnotatedBranch>[] | null;
};

export function extractUpdateState(
  state: FormBranchesState,
  formData: FormData,
): FormBranchesSaveState {
  const {
    featureConfigIds,
    warnFeatureSchema,
    isRollout,
    referenceBranch,
    treatmentBranches,
    preventPrefConflicts,
    isLocalized,
    localizations,
  } = state;

  if (!referenceBranch) {
    throw new UpdateStateError(CONTROL_BRANCH_REQUIRED_ERROR);
  }

  const extractedState = {
    featureConfigIds,
    warnFeatureSchema,
    isRollout,
    isLocalized,
    localizations,
    referenceBranch: extractUpdateBranch(
      referenceBranch,
      formData.referenceBranch,
    ),
    treatmentBranches:
      treatmentBranches === null
        ? []
        : treatmentBranches.map(
            (branch, idx) =>
              extractUpdateBranch(branch, formData.treatmentBranches?.[idx]!)!,
          ),
    preventPrefConflicts,
  };
  return extractedState;
}

export function extractUpdateBranch(
  branch: AnnotatedBranch,
  formBranch: Partial<FormData["referenceBranch"]> | null,
): FormBranchesSaveState["referenceBranch"] {
  const merged = { ...branch, ...formBranch };
  const screenshots = branch.screenshots?.map((branchScreenshot, idx) =>
    extractUpdateScreenshot(branchScreenshot!, formBranch!.screenshots![idx]!),
  );
  const featureValues = branch.featureValues?.map((branchFeatureValue, idx) =>
    extractUpdateFeatureValue(
      branchFeatureValue!,
      formBranch?.featureValues?.[idx] ?? {},
    ),
  );
  return {
    // Branch ID should be read-only with respect to the form data
    id: branch.id,
    name: merged.name,
    description: merged.description,
    ratio: merged.ratio,
    featureValues,
    screenshots,
  };
}

export function extractUpdateFeatureValue(
  branchFeatureValue: BranchFeatureValueInput,
  { featureConfig, value }: BranchFeatureValueInput,
): BranchFeatureValueInput {
  return {
    featureConfig,
    value,
  };
}

export function extractUpdateScreenshot(
  branchScreenshot: BranchScreenshotInput,
  { description, image }: BranchScreenshotInput,
): BranchScreenshotInput {
  return {
    // Branch screenshot ID should be read-only with respect to the form data
    id: branchScreenshot!.id,
    description,
    // An image of type string represents an already-uploaded resource, so
    // treat it as undefined for purposes of saving an update.
    image: typeof image === "string" ? undefined : image,
  };
}
