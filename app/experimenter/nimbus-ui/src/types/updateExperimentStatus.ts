/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { UpdateExperimentStatusInput, NimbusExperimentStatus } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: updateExperimentStatus
// ====================================================

export interface updateExperimentStatus_updateExperimentStatus_nimbusExperiment {
  __typename: "NimbusExperimentType";
  status: NimbusExperimentStatus | null;
}

export interface updateExperimentStatus_updateExperimentStatus {
  __typename: "UpdateExperimentStatus";
  clientMutationId: string | null;
  message: any | null;
  status: number | null;
  nimbusExperiment: updateExperimentStatus_updateExperimentStatus_nimbusExperiment | null;
}

export interface updateExperimentStatus {
  updateExperimentStatus: updateExperimentStatus_updateExperimentStatus | null;
}

export interface updateExperimentStatusVariables {
  input: UpdateExperimentStatusInput;
}
