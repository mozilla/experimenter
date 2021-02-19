/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExperimentInput } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: createExperiment
// ====================================================

export interface createExperiment_createExperiment_nimbusExperiment {
  slug: string;
}

export interface createExperiment_createExperiment {
  message: ObjectField | null;
  nimbusExperiment: createExperiment_createExperiment_nimbusExperiment | null;
}

export interface createExperiment {
  createExperiment: createExperiment_createExperiment | null;
}

export interface createExperimentVariables {
  input: ExperimentInput;
}
