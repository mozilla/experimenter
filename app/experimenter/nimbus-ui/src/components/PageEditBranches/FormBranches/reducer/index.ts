/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMemo, useReducer } from "react";
import { ExperimentInput } from "../../../../types/globalTypes";
import { formBranchesActionReducer } from "./actions";
import { createInitialState } from "./state";
import { extractUpdateState } from "./update";

export { REFERENCE_BRANCH_IDX } from "./actions";
export type { AnnotatedBranch } from "./state";
export type { FormBranchesSaveState } from "./update";

export function useFormBranchesReducer(experiment: ExperimentInput) {
  const [formBranchesState, dispatch] = useReducer(
    formBranchesActionReducer,
    useMemo(
      () =>
        createInitialState({
          featureConfigs: experiment.featureConfigs,
          referenceBranch: experiment.referenceBranch,
          treatmentBranches: experiment.treatmentBranches,
        }),
      [experiment],
    ),
  );
  return [
    formBranchesState,
    (formValues: Parameters<typeof extractUpdateState>[1]) =>
      extractUpdateState(formBranchesState, formValues),
    dispatch,
  ] as const;
}

export default useFormBranchesReducer;
