/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExperimentInput } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: updateExperimentProbeSets
// ====================================================

export interface updateExperimentProbeSets_updateExperiment_nimbusExperiment_primaryProbeSets {
  __typename: "NimbusProbeSetType";
  id: string;
}

export interface updateExperimentProbeSets_updateExperiment_nimbusExperiment_secondaryProbeSets {
  __typename: "NimbusProbeSetType";
  id: string;
}

export interface updateExperimentProbeSets_updateExperiment_nimbusExperiment {
  __typename: "NimbusExperimentType";
  id: number | null;
  primaryProbeSets: (updateExperimentProbeSets_updateExperiment_nimbusExperiment_primaryProbeSets | null)[] | null;
  secondaryProbeSets: (updateExperimentProbeSets_updateExperiment_nimbusExperiment_secondaryProbeSets | null)[] | null;
}

export interface updateExperimentProbeSets_updateExperiment {
  __typename: "UpdateExperiment";
  nimbusExperiment: updateExperimentProbeSets_updateExperiment_nimbusExperiment | null;
  message: ObjectField | null;
  status: number | null;
}

export interface updateExperimentProbeSets {
  updateExperiment: updateExperimentProbeSets_updateExperiment | null;
}

export interface updateExperimentProbeSetsVariables {
  input: ExperimentInput;
}
