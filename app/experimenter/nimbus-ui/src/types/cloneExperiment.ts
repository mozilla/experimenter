/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExperimentCloneInput } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: cloneExperiment
// ====================================================

export interface cloneExperiment_cloneExperiment_nimbusExperiment {
  slug: string;
}

export interface cloneExperiment_cloneExperiment {
  message: ObjectField | null;
  nimbusExperiment: cloneExperiment_cloneExperiment_nimbusExperiment | null;
}

export interface cloneExperiment {
  cloneExperiment: cloneExperiment_cloneExperiment | null;
}

export interface cloneExperimentVariables {
  input: ExperimentCloneInput;
}
