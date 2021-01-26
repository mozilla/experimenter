/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExperimentInput } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: updateExperimentBranches
// ====================================================

export interface updateExperimentBranches_updateExperiment_nimbusExperiment_featureConfig {
  __typename: "NimbusFeatureConfigType";
  name: string;
}

export interface updateExperimentBranches_updateExperiment_nimbusExperiment_referenceBranch {
  __typename: "NimbusBranchType";
  name: string;
  description: string;
  ratio: number;
}

export interface updateExperimentBranches_updateExperiment_nimbusExperiment_treatmentBranches {
  __typename: "NimbusBranchType";
  name: string;
  description: string;
  ratio: number;
}

export interface updateExperimentBranches_updateExperiment_nimbusExperiment {
  __typename: "NimbusExperimentType";
  id: number | null;
  featureConfig: updateExperimentBranches_updateExperiment_nimbusExperiment_featureConfig | null;
  referenceBranch: updateExperimentBranches_updateExperiment_nimbusExperiment_referenceBranch | null;
  treatmentBranches: (updateExperimentBranches_updateExperiment_nimbusExperiment_treatmentBranches | null)[] | null;
}

export interface updateExperimentBranches_updateExperiment {
  __typename: "UpdateExperiment";
  message: ObjectField | null;
  status: number | null;
  nimbusExperiment: updateExperimentBranches_updateExperiment_nimbusExperiment | null;
}

export interface updateExperimentBranches {
  updateExperiment: updateExperimentBranches_updateExperiment | null;
}

export interface updateExperimentBranchesVariables {
  input: ExperimentInput;
}
