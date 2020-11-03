import { useReducer, useMemo } from "react";
import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_treatmentBranches,
} from "../../types/getExperiment";

export function useFormBranchesReducer({
  featureConfig,
  referenceBranch,
  treatmentBranches,
}: getExperiment_experimentBySlug) {
  const initialState = useMemo(() => {
    let lastId = 0;

    const equalRatio =
      treatmentBranches !== null &&
      treatmentBranches?.every(
        (branch) => branch?.ratio === referenceBranch?.ratio,
      );

    const annotatedReferenceBranch =
      referenceBranch === null
        ? null
        : annotateBranch("reference", referenceBranch!);

    const annotatedTreatmentBranches = !Array.isArray(treatmentBranches)
      ? null
      : treatmentBranches.map((branch) => annotateBranch(lastId++, branch!));

    return {
      lastId,
      equalRatio,
      featureConfig,
      referenceBranch: annotatedReferenceBranch,
      treatmentBranches: annotatedTreatmentBranches,
    };
  }, [featureConfig, referenceBranch, treatmentBranches]);
  return useReducer(formBranchesReducer, initialState);
}

export function formBranchesReducer(
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
    default:
      return state;
  }
}

export function extractSaveState(
  state: FormBranchesState,
): FormBranchesSaveState {
  const { featureConfig, referenceBranch, treatmentBranches } = state;
  return {
    featureConfig,
    referenceBranch: stripOneAnnotatedBranch(referenceBranch),
    treatmentBranches: stripAnnotatedBranches(treatmentBranches),
  };
}

export const REFERENCE_BRANCH_IDX = -1;

export type FormBranchesState = Pick<
  getExperiment_experimentBySlug,
  "featureConfig"
> & {
  referenceBranch: null | AnnotatedBranch;
  treatmentBranches: null | AnnotatedBranch[];
  equalRatio: boolean;
  lastId: number;
};

export type FormBranchesSaveState = Pick<
  getExperiment_experimentBySlug,
  "featureConfig" | "referenceBranch" | "treatmentBranches"
>;

export type FormBranchesAction =
  | AddBranchAction
  | RemoveBranchAction
  | UpdateBranchAction
  | RemoveFeatureConfigAction
  | SetEqualRatioAction
  | SetFeatureConfigAction;

type AddBranchAction = {
  type: "addBranch";
};

function addBranch(state: FormBranchesState) {
  let { lastId, referenceBranch, treatmentBranches } = state;
  lastId++;

  if (referenceBranch === null) {
    referenceBranch = makeBranch(lastId, "New control");
  } else {
    treatmentBranches = [
      ...(treatmentBranches || []),
      makeBranch(state.lastId, `New treatment ${lastId}`),
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
    treatmentBranches = (treatmentBranches || []).slice();
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
  return {
    ...state,
    featureConfig: null,
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

export type AnnotatedBranch = getExperiment_experimentBySlug_treatmentBranches & {
  __key: string;
};

function annotateBranch(
  lastId: number | string,
  branch: getExperiment_experimentBySlug_treatmentBranches,
) {
  return {
    ...branch,
    __key: `branch-${lastId}`,
  };
}

export function stripOneAnnotatedBranch(branch: null | AnnotatedBranch) {
  if (!branch) return null;
  const {
    __key, // eslint-disable-line @typescript-eslint/no-unused-vars
    ...strippedBranch
  } = branch;
  return strippedBranch;
}

export function stripAnnotatedBranches(
  branches: null | AnnotatedBranch[],
): getExperiment_experimentBySlug["treatmentBranches"] {
  if (branches === null) return null;
  return branches.map(stripOneAnnotatedBranch);
}

function makeBranch(lastId: number, name: string): AnnotatedBranch {
  return {
    __typename: "NimbusBranchType" as const,
    __key: `branch-${lastId}`,
    name,
    slug: "",
    description: "",
    ratio: 1,
    featureValue: null,
    featureEnabled: true,
  };
}

export default formBranchesReducer;
