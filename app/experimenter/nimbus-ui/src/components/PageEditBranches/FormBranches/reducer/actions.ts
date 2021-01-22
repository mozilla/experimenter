/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import {
  AnnotatedBranch,
  createAnnotatedBranch,
  FormBranchesState,
} from "./state";
import { FormData } from "./update";

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
    case "commitFormData":
      return commitFormData(state, action);
    default:
      return state;
  }
}

export type FormBranchesAction =
  | AddBranchAction
  | RemoveBranchAction
  | RemoveFeatureConfigAction
  | SetEqualRatioAction
  | SetFeatureConfigAction
  | SetSubmitErrorsAction
  | ClearSubmitErrorsAction
  | CommitFormDataAction;

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

type RemoveFeatureConfigAction = {
  type: "removeFeatureConfig";
};

function removeFeatureConfig(state: FormBranchesState) {
  let { referenceBranch, treatmentBranches } = state;

  if (referenceBranch) {
    referenceBranch = {
      ...referenceBranch,
      featureEnabled: false,
      featureValue: null,
    };
  }

  if (Array.isArray(treatmentBranches)) {
    treatmentBranches = treatmentBranches.map(
      (branch) =>
        branch && { ...branch, featureEnabled: false, featureValue: null },
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
  submitErrors: Record<string, any> | null;
};

function setSubmitErrors(
  state: FormBranchesState,
  action: SetSubmitErrorsAction,
) {
  let { referenceBranch, treatmentBranches } = state;
  const { submitErrors } = action;
  const globalErrors = [];

  if (!submitErrors) {
    return state;
  }

  for (const name of ["*", "feature_config"]) {
    if (Array.isArray(submitErrors[name])) {
      globalErrors.push(...submitErrors[name]);
    }
  }

  if (referenceBranch && submitErrors["reference_branch"]) {
    referenceBranch = {
      ...referenceBranch,
      // TODO: EXP-614 submitErrors type is any, but in practical use it's AnnotatedBranch["errors"]
      errors: (submitErrors["reference_branch"] ||
        {}) as AnnotatedBranch["errors"],
    };
  }

  if (treatmentBranches && submitErrors["treatment_branches"]) {
    treatmentBranches = treatmentBranches.map((treatmentBranch, idx) => ({
      ...treatmentBranch,
      errors: submitErrors["treatment_branches"][idx] || {},
    }));
  }

  return {
    ...state,
    globalErrors,
    referenceBranch,
    treatmentBranches,
  };
}

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

type CommitFormDataAction = {
  type: "commitFormData";
  formData: FormData;
};

function commitFormData(
  state: FormBranchesState,
  action: CommitFormDataAction,
) {
  const { formData } = action;
  let { referenceBranch, treatmentBranches } = state;

  if (referenceBranch) {
    referenceBranch = {
      ...referenceBranch,
      ...formData.referenceBranch,
    };
  }

  if (treatmentBranches) {
    treatmentBranches = treatmentBranches.map((treatmentBranch, idx) => ({
      ...treatmentBranch,
      ...formData.treatmentBranches?.[idx],
    }));
  }

  return {
    ...state,
    referenceBranch,
    treatmentBranches,
  };
}
