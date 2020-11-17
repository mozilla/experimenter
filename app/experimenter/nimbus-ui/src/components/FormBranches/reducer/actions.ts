/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { updateExperimentBranches_updateExperimentBranches } from "../../../types/updateExperimentBranches";
import {
  AnnotatedBranch,
  FormBranchesState,
  createAnnotatedBranch,
} from "./state";
import snakeToCamelCase from "../../../lib/snakeToCamelCase";

export const REFERENCE_BRANCH_IDX = -1;

export function formBranchesActionReducer(
  state: FormBranchesState,
  action: FormBranchesAction,
): FormBranchesState {
  switch (action.type) {
    case "addBranch":
      return addBranch(state);
    case "removeBranch":
      return removeBranch(state, action);
    case "updateBranch":
      return updateBranch(state, action);
    case "removeFeatureConfig":
      return removeFeatureConfig(state);
    case "setFeatureConfig":
      return setFeatureConfig(state, action);
    case "setEqualRatio":
      return setEqualRatio(state, action);
    case "setSubmitErrors":
      return setSubmitErrors(state, action);
    case "clearSubmitErrors":
      return clearSubmitErrors(state);
    case "resetDirtyBranches":
      return resetDirtyBranches(state);
    default:
      return state;
  }
}

export type FormBranchesAction =
  | AddBranchAction
  | RemoveBranchAction
  | UpdateBranchAction
  | RemoveFeatureConfigAction
  | SetEqualRatioAction
  | SetFeatureConfigAction
  | SetSubmitErrorsAction
  | ClearSubmitErrorsAction
  | ResetDirtyBranchesAction;

type AddBranchAction = {
  type: "addBranch";
};

function addBranch(state: FormBranchesState) {
  let { lastId, referenceBranch, treatmentBranches } = state;
  lastId++;

  if (referenceBranch === null) {
    referenceBranch = createAnnotatedBranch(lastId, "New control");
  } else {
    treatmentBranches = [
      ...(treatmentBranches || []),
      createAnnotatedBranch(state.lastId, `New treatment ${lastId}`),
    ];
  }

  return {
    ...state,
    lastId,
    referenceBranch,
    treatmentBranches,
  };
}

type RemoveBranchAction = {
  type: "removeBranch";
  idx: number;
};

function removeBranch(state: FormBranchesState, { idx }: RemoveBranchAction) {
  const treatmentBranches = state.treatmentBranches || [];
  return {
    ...state,
    treatmentBranches: [
      ...treatmentBranches.slice(0, idx),
      ...treatmentBranches.slice(idx + 1),
    ],
  };
}

type UpdateBranchAction = {
  type: "updateBranch";
  idx: number;
  value: AnnotatedBranch;
};

function updateBranch(
  state: FormBranchesState,
  { idx, value }: UpdateBranchAction,
) {
  let { referenceBranch, treatmentBranches } = state;
  const updatedBranch = { ...value };
  if (idx === REFERENCE_BRANCH_IDX) {
    referenceBranch = updatedBranch;
  } else {
    treatmentBranches = [...treatmentBranches!];
    treatmentBranches[idx] = updatedBranch;
  }
  return {
    ...state,
    referenceBranch,
    treatmentBranches,
  };
}

type RemoveFeatureConfigAction = {
  type: "removeFeatureConfig";
};

function removeFeatureConfig(state: FormBranchesState) {
  let { referenceBranch, treatmentBranches } = state;

  if (referenceBranch) {
    referenceBranch = {
      ...referenceBranch,
      featureEnabled: false,
    };
  }

  if (Array.isArray(treatmentBranches)) {
    treatmentBranches = treatmentBranches.map(
      (branch) => branch && { ...branch, featureEnabled: false },
    );
  }

  return {
    ...state,
    featureConfig: null,
    referenceBranch,
    treatmentBranches,
  };
}

type SetFeatureConfigAction = {
  type: "setFeatureConfig";
  value: FormBranchesState["featureConfig"];
};

function setFeatureConfig(
  state: FormBranchesState,
  { value: featureConfig }: SetFeatureConfigAction,
) {
  if (!featureConfig) return removeFeatureConfig(state);
  return {
    ...state,
    featureConfig,
  };
}

type SetEqualRatioAction = {
  type: "setEqualRatio";
  value: FormBranchesState["equalRatio"];
};

function setEqualRatio(
  state: FormBranchesState,
  { value: equalRatio }: SetEqualRatioAction,
) {
  let { referenceBranch, treatmentBranches } = state;
  if (equalRatio) {
    if (referenceBranch !== null) {
      referenceBranch = { ...referenceBranch, ratio: 1 };
    }
    if (Array.isArray(treatmentBranches)) {
      treatmentBranches = treatmentBranches.map(
        (treatmentBranch) =>
          treatmentBranch && {
            ...treatmentBranch,
            ratio: 1,
          },
      );
    }
  }
  return {
    ...state,
    equalRatio,
    referenceBranch,
    treatmentBranches,
  };
}

type SetSubmitErrorsAction = {
  type: "setSubmitErrors";
  submitErrors: updateExperimentBranches_updateExperimentBranches["message"];
};

function setSubmitErrors(
  state: FormBranchesState,
  action: SetSubmitErrorsAction,
) {
  let { referenceBranch, treatmentBranches } = state;
  const { submitErrors } = action;
  const globalErrors = [];

  for (const name of ["*", "feature_config"]) {
    if (Array.isArray(submitErrors[name])) {
      globalErrors.push(...submitErrors[name]);
    }
  }

  if (referenceBranch && submitErrors["reference_branch"]) {
    referenceBranch = {
      ...referenceBranch,
      // TODO: submitErrors type is any, but in practical use it's AnnotatedBranch["errors"]
      errors: normalizeFieldNames(
        submitErrors["reference_branch"],
      ) as AnnotatedBranch["errors"],
    };
  }

  if (treatmentBranches && submitErrors["treatment_branches"]) {
    treatmentBranches = treatmentBranches.map((treatmentBranch, idx) => ({
      ...treatmentBranch,
      errors: normalizeFieldNames(submitErrors["treatment_branches"][idx]),
    }));
  }

  return {
    ...state,
    globalErrors,
    referenceBranch,
    treatmentBranches,
  };
}

// Server-side field names are in snake-case, client-side field names are
// in camel-case, this utility converts from server to client convention
const normalizeFieldNames = (
  errors: Record<string, string[]>,
): Record<string, string[]> =>
  Object.entries(errors).reduce(
    (acc, [key, value]) => ({
      ...acc,
      [snakeToCamelCase(key)]: value,
    }),
    {},
  );

type ClearSubmitErrorsAction = {
  type: "clearSubmitErrors";
};

function clearSubmitErrors(state: FormBranchesState) {
  let { referenceBranch, treatmentBranches } = state;
  const globalErrors = [] as string[];

  if (referenceBranch) {
    referenceBranch = { ...referenceBranch, errors: {} };
  }

  if (treatmentBranches) {
    treatmentBranches = treatmentBranches.map((treatmentBranch) => ({
      ...treatmentBranch,
      errors: {},
    }));
  }

  return {
    ...state,
    globalErrors,
    referenceBranch,
    treatmentBranches,
  };
}

type ResetDirtyBranchesAction = {
  type: "resetDirtyBranches";
};

function resetDirtyBranches(state: FormBranchesState) {
  let { referenceBranch, treatmentBranches } = state;

  if (referenceBranch) {
    referenceBranch = { ...referenceBranch, isDirty: false };
  }

  if (treatmentBranches) {
    treatmentBranches = treatmentBranches.map((treatmentBranch) => ({
      ...treatmentBranch,
      isDirty: false,
    }));
  }

  return {
    ...state,
    referenceBranch,
    treatmentBranches,
  };
}
