/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { UpdateExperimentBranchesInput } from "../../../types/globalTypes";
import { FormBranchesState, AnnotatedBranch } from "./state";
import { REFERENCE_BRANCH_IDX } from "./index";

export type FormBranchesSaveState = Pick<
  UpdateExperimentBranchesInput,
  "featureConfigId" | "referenceBranch" | "treatmentBranches"
>;

export class UpdateStateError extends Error {}

export type FormValue = { idx: number; isValid: boolean } & Partial<
  FormBranchesSaveState["referenceBranch"]
>;

export function extractUpdateState(
  state: FormBranchesState,
  formValues: FormValue[],
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
      formValues,
      REFERENCE_BRANCH_IDX,
    ),
    treatmentBranches:
      treatmentBranches === null
        ? []
        : treatmentBranches.map((branch, idx) =>
            extractUpdateBranch(branch, formValues, idx),
          ),
  };
}

export function extractUpdateBranch(
  branch: AnnotatedBranch,
  formValues: FormValue[],
  idx: number,
): FormBranchesSaveState["referenceBranch"] {
  const formValue = formValues.find((value) => value.idx === idx);
  const {
    /* eslint-disable @typescript-eslint/no-unused-vars */
    __typename,
    idx: ignoredIdx,
    key,
    errors,
    isValid,
    isDirty,
    slug,
    /* eslint-enable @typescript-eslint/no-unused-vars */
    ...strippedBranch
  } = { ...branch, ...formValue };
  return strippedBranch;
}
