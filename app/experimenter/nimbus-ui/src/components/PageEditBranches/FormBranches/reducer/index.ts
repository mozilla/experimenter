/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMemo, useReducer } from "react";
import { formBranchesActionReducer } from "src/components/PageEditBranches/FormBranches/reducer/actions";
import { createInitialState } from "src/components/PageEditBranches/FormBranches/reducer/state";
import { extractUpdateState } from "src/components/PageEditBranches/FormBranches/reducer/update";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

export { REFERENCE_BRANCH_IDX } from "./actions";
export type { AnnotatedBranch } from "./state";
export type { FormBranchesSaveState } from "./update";

export function useFormBranchesReducer(
  experiment: getExperiment_experimentBySlug,
) {
  const [formBranchesState, dispatch] = useReducer(
    formBranchesActionReducer,
    useMemo(() => createInitialState(experiment), [experiment]),
  );
  return [
    formBranchesState,
    (formValues: Parameters<typeof extractUpdateState>[1]) =>
      extractUpdateState(formBranchesState, formValues),
    dispatch,
  ] as const;
}

export default useFormBranchesReducer;
