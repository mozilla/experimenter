/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExperimentIdInput } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: endExperiment
// ====================================================

export interface endExperiment_endExperiment {
  __typename: "EndExperiment";
  message: ObjectField | null;
}

export interface endExperiment {
  endExperiment: endExperiment_endExperiment | null;
}

export interface endExperimentVariables {
  input: ExperimentIdInput;
}
