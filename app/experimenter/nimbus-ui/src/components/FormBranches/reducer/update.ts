/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { UpdateExperimentBranchesInput } from "../../../types/globalTypes";
import { FormBranchesState, AnnotatedBranch } from "./state";

export type FormBranchesSaveState = Pick<
  UpdateExperimentBranchesInput,
  "featureConfigId" | "referenceBranch" | "treatmentBranches"
>;

export class UpdateStateError extends Error {}

export function extractUpdateState(
  state: FormBranchesState,
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
    referenceBranch: extractUpdateBranch(referenceBranch),
    treatmentBranches:
      treatmentBranches === null
        ? []
        : treatmentBranches.map(extractUpdateBranch),
  };
}

export function extractUpdateBranch(
  branch: AnnotatedBranch,
): FormBranchesSaveState["referenceBranch"] {
  const {
    /* eslint-disable @typescript-eslint/no-unused-vars */
    __typename,
    key,
    errors,
    isValid,
    isDirty,
    slug,
    /* eslint-enable @typescript-eslint/no-unused-vars */
    ...strippedBranch
  } = branch;
  return strippedBranch;
}
