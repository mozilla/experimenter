/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { BranchScreenshotInput } from "../../../../types/globalTypes";
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
    case "setIsRollout":
      return setIsRollout(state, action);
    case "setFeatureConfigs":
      return setFeatureConfigs(state, action);
    case "setwarnFeatureSchema":
      return setwarnFeatureSchema(state, action);
    case "setEqualRatio":
      return setEqualRatio(state, action);
    case "setSubmitErrors":
      return setSubmitErrors(state, action);
    case "clearSubmitErrors":
      return clearSubmitErrors(state);
    case "commitFormData":
      return commitFormData(state, action);
    case "addScreenshotToBranch":
      return addScreenshotToBranch(state, action);
    case "removeScreenshotFromBranch":
      return removeScreenshotFromBranch(state, action);
    default:
      return state;
  }
}

export type FormBranchesAction =
  | AddBranchAction
  | RemoveBranchAction
  | SetEqualRatioAction
  | SetFeatureConfigsAction
  | SetwarnFeatureSchemaAction
  | SetIsRolloutAction
  | SetSubmitErrorsAction
  | ClearSubmitErrorsAction
  | CommitFormDataAction
  | AddScreenshotToBranchAction
  | RemoveScreenshotFromBranchAction;

type AddBranchAction = {
  type: "addBranch";
};

function addBranch(state: FormBranchesState): FormBranchesState {
  let { lastId, referenceBranch, treatmentBranches } = state;
  lastId++;

  if (referenceBranch === null) {
    referenceBranch = createAnnotatedBranch(lastId, "control");
  } else {
    treatmentBranches = [
      ...(treatmentBranches || []),
      createAnnotatedBranch(
        state.lastId,
        // 65 is A, but we generate a control, so start at 64
        `Treatment ${String.fromCharCode(64 + lastId)}`,
      ),
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

function removeBranch(
  state: FormBranchesState,
  { idx }: RemoveBranchAction,
): FormBranchesState {
  const treatmentBranches = state.treatmentBranches || [];
  return {
    ...state,
    treatmentBranches: [
      ...treatmentBranches.slice(0, idx),
      ...treatmentBranches.slice(idx + 1),
    ],
  };
}

type SetFeatureConfigsAction = {
  type: "setFeatureConfigs";
  value: FormBranchesState["featureConfigIds"];
};

function setFeatureConfigs(
  state: FormBranchesState,
  { value: featureConfigIds }: SetFeatureConfigsAction,
): FormBranchesState {
  return {
    ...state,
    featureConfigIds: featureConfigIds || null,
  };
}

type SetwarnFeatureSchemaAction = {
  type: "setwarnFeatureSchema";
  value: FormBranchesState["warnFeatureSchema"];
};

type SetIsRolloutAction = {
  type: "setIsRollout";
  value: FormBranchesState["isRollout"];
};

function setIsRollout(
  state: FormBranchesState,
  { value: isRollout }: SetIsRolloutAction,
) {
  let { treatmentBranches } = state;
  if (isRollout) {
    treatmentBranches = [];
  }
  return {
    ...state,
    isRollout,
    treatmentBranches,
  };
}

function setwarnFeatureSchema(
  state: FormBranchesState,
  { value: warnFeatureSchema }: SetwarnFeatureSchemaAction,
): FormBranchesState {
  return {
    ...state,
    warnFeatureSchema,
  };
}

type SetEqualRatioAction = {
  type: "setEqualRatio";
  value: FormBranchesState["equalRatio"];
};

function setEqualRatio(
  state: FormBranchesState,
  { value: equalRatio }: SetEqualRatioAction,
): FormBranchesState {
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
): FormBranchesState {
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

function clearSubmitErrors(state: FormBranchesState): FormBranchesState {
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
): FormBranchesState {
  const { formData } = action;
  let { referenceBranch, treatmentBranches } = state;

  if (referenceBranch) {
    referenceBranch = branchUpdatedWithFormData(
      state,
      referenceBranch,
      formData.referenceBranch,
    );
  }

  if (treatmentBranches) {
    treatmentBranches = treatmentBranches.map((treatmentBranch, idx) =>
      branchUpdatedWithFormData(
        state,
        treatmentBranch,
        formData.treatmentBranches?.[idx],
      ),
    );
  }

  return {
    ...state,
    referenceBranch,
    treatmentBranches,
  };
}

function branchUpdatedWithFormData(
  state: FormBranchesState,
  branch: AnnotatedBranch,
  formData: Partial<AnnotatedBranch> | null | undefined,
): AnnotatedBranch {
  const screenshots = branch.screenshots?.map((screenshot, idx) => {
    const { description, image } = formData?.screenshots?.[idx] || {};
    return {
      id: screenshot?.id,
      description,
      image,
    };
  });
  const featureValues = state.featureConfigIds?.map((featureConfigId, idx) => {
    const { enabled, value } = formData?.featureValues?.[idx] || {};
    return {
      featureConfigId,
      enabled,
      value,
    };
  });
  return {
    ...branch,
    ...formData,
    screenshots,
    featureValues,
  };
}

type AddScreenshotToBranchAction = {
  type: "addScreenshotToBranch";
  branchIdx: number;
};

function addScreenshotToBranch(
  state: FormBranchesState,
  action: AddScreenshotToBranchAction,
): FormBranchesState {
  const { branchIdx } = action;
  let { referenceBranch, treatmentBranches } = state;

  const newScreenshot: BranchScreenshotInput = { description: "", image: null };

  if (branchIdx === REFERENCE_BRANCH_IDX && referenceBranch) {
    referenceBranch = {
      ...referenceBranch,
      screenshots: [...(referenceBranch.screenshots || []), newScreenshot],
    };
  } else if (treatmentBranches) {
    treatmentBranches = withModifiedBranch(
      treatmentBranches,
      branchIdx,
      (selectedBranch) => ({
        ...selectedBranch,
        screenshots: [...(selectedBranch.screenshots || []), newScreenshot],
      }),
    );
  }

  return {
    ...state,
    referenceBranch,
    treatmentBranches,
  };
}

type RemoveScreenshotFromBranchAction = {
  type: "removeScreenshotFromBranch";
  branchIdx: number;
  screenshotIdx: number;
};

function removeScreenshotFromBranch(
  state: FormBranchesState,
  action: RemoveScreenshotFromBranchAction,
): FormBranchesState {
  const { branchIdx, screenshotIdx } = action;
  let { referenceBranch, treatmentBranches } = state;

  if (branchIdx === REFERENCE_BRANCH_IDX && referenceBranch) {
    referenceBranch = {
      ...referenceBranch,
      screenshots: withoutScreenshot(
        referenceBranch.screenshots,
        screenshotIdx,
      ),
    };
  } else if (treatmentBranches) {
    treatmentBranches = withModifiedBranch(
      treatmentBranches,
      branchIdx,
      (selectedBranch) => ({
        ...selectedBranch,
        screenshots: withoutScreenshot(
          selectedBranch.screenshots,
          screenshotIdx,
        ),
      }),
    );
  }

  return {
    ...state,
    referenceBranch,
    treatmentBranches,
  };
}

function withModifiedBranch(
  branches: AnnotatedBranch[] | null,
  branchIdx: number,
  modifier: (selectedBranch: AnnotatedBranch) => AnnotatedBranch,
) {
  const selectedBranch = branches?.[branchIdx];
  if (selectedBranch) {
    return [
      ...branches!.slice(0, branchIdx),
      modifier(selectedBranch),
      ...branches!.slice(branchIdx + 1),
    ];
  }
  return branches;
}

function withoutScreenshot(
  screenshots: (BranchScreenshotInput | null)[] | null | undefined,
  idx: number,
) {
  if (!screenshots) return [];
  return [...screenshots.slice(0, idx), ...screenshots.slice(idx + 1)];
}
