/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { ExperimentInput } from "../../../../types/globalTypes";
import { AnnotatedBranch, FormBranchesState } from "./state";

export type FormBranchesSaveState = Pick<
  ExperimentInput,
  "featureConfigId" | "referenceBranch" | "treatmentBranches"
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
  const { featureConfig, referenceBranch, treatmentBranches } = state;

  if (!referenceBranch) {
    throw new UpdateStateError("Control branch is required");
  }

  // issue #3954: Need to parse string IDs into numbers
  const featureConfigId =
    featureConfig === null ? null : parseInt(featureConfig.id, 10);

  return {
    featureConfigId,
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
  formBranch: Partial<FormBranchesSaveState["referenceBranch"]> | null,
): FormBranchesSaveState["referenceBranch"] {
  const merged = { ...branch, ...formBranch };
  return {
    name: merged.name,
    description: merged.description,
    ratio: merged.ratio,
    featureValue: merged.featureValue,
    // HACK: for some reason in tests, this ends up as "true" or undefined
    // rather than a boolean.
    featureEnabled: !!merged.featureEnabled,
  };
}
