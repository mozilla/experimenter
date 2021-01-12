/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExperimentInput, NimbusExperimentStatus } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: updateExperimentStatus
// ====================================================

export interface updateExperimentStatus_updateExperiment_nimbusExperiment {
  __typename: "NimbusExperimentType";
  status: NimbusExperimentStatus | null;
}

export interface updateExperimentStatus_updateExperiment {
  __typename: "UpdateExperiment";
  message: ObjectField | null;
  status: number | null;
  nimbusExperiment: updateExperimentStatus_updateExperiment_nimbusExperiment | null;
}

export interface updateExperimentStatus {
  updateExperiment: updateExperimentStatus_updateExperiment | null;
}

export interface updateExperimentStatusVariables {
  input: ExperimentInput;
}
