/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { UpdateExperimentBranchesInput } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: updateExperimentBranches
// ====================================================

export interface updateExperimentBranches_updateExperimentBranches_nimbusExperiment_featureConfig {
  __typename: "NimbusFeatureConfigType";
  name: string;
}

export interface updateExperimentBranches_updateExperimentBranches_nimbusExperiment_referenceBranch {
  __typename: "NimbusBranchType";
  name: string;
  description: string;
  ratio: number;
}

export interface updateExperimentBranches_updateExperimentBranches_nimbusExperiment_treatmentBranches {
  __typename: "NimbusBranchType";
  name: string;
  description: string;
  ratio: number;
}

export interface updateExperimentBranches_updateExperimentBranches_nimbusExperiment {
  __typename: "NimbusExperimentType";
  id: string;
  featureConfig: updateExperimentBranches_updateExperimentBranches_nimbusExperiment_featureConfig | null;
  referenceBranch: updateExperimentBranches_updateExperimentBranches_nimbusExperiment_referenceBranch | null;
  treatmentBranches: (updateExperimentBranches_updateExperimentBranches_nimbusExperiment_treatmentBranches | null)[] | null;
}

export interface updateExperimentBranches_updateExperimentBranches {
  __typename: "UpdateExperimentBranches";
  clientMutationId: string | null;
  message: any | null;
  status: number | null;
  nimbusExperiment: updateExperimentBranches_updateExperimentBranches_nimbusExperiment | null;
}

export interface updateExperimentBranches {
  updateExperimentBranches: updateExperimentBranches_updateExperimentBranches | null;
}

export interface updateExperimentBranchesVariables {
  input: UpdateExperimentBranchesInput;
}
