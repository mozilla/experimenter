/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { CONTROL_BRANCH_REQUIRED_ERROR } from "../../../../lib/constants";
import {
  BranchScreenshotType,
  ExperimentInput,
} from "../../../../types/globalTypes";
import { AnnotatedBranch, FormBranchesState } from "./state";

export type FormBranchesSaveState = Pick<
  ExperimentInput,
  | "featureConfigId"
  | "warnFeatureSchema"
  | "referenceBranch"
  | "treatmentBranches"
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
    featureConfig,
    warnFeatureSchema,
    referenceBranch,
    treatmentBranches,
  } = state;

  if (!referenceBranch) {
    throw new UpdateStateError(CONTROL_BRANCH_REQUIRED_ERROR);
  }

  const featureConfigId = featureConfig === null ? null : featureConfig.id;

  return {
    featureConfigId,
    warnFeatureSchema,
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
  };
}

export function extractUpdateBranch(
  branch: AnnotatedBranch,
  formBranch: Partial<FormData["referenceBranch"]> | null,
): FormBranchesSaveState["referenceBranch"] {
  const merged = { ...branch, ...formBranch };
  const screenshots = branch.screenshots?.map((branchScreenshot, idx) =>
    extractUpdateScreenshot(branchScreenshot!, formBranch!.screenshots![idx]!),
  );
  return {
    // Branch ID should be read-only with respect to the form data
    id: branch.id,
    name: merged.name,
    description: merged.description,
    ratio: merged.ratio,
    featureValue: merged.featureValue,
    // HACK: for some reason in tests, this ends up as "true" or undefined
    // rather than a boolean.
    featureEnabled: !!merged.featureEnabled,
    screenshots,
  };
}

export function extractUpdateScreenshot(
  branchScreenshot: BranchScreenshotType,
  { description, image }: BranchScreenshotType,
): BranchScreenshotType {
  return {
    // Branch screenshot ID should be read-only with respect to the form data
    id: branchScreenshot!.id,
    description,
    // An image of type string represents an already-uploaded resource, so
    // treat it as undefined for purposes of saving an update.
    image: typeof image === "string" ? undefined : image,
  };
}
