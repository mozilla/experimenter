/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { UpdateExperimentProbeSetsInput } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: updateExperimentProbeSets
// ====================================================

export interface updateExperimentProbeSets_updateExperimentProbeSets_nimbusExperiment_primaryProbeSets {
  __typename: "NimbusProbeSetType";
  id: string;
  name: string;
}

export interface updateExperimentProbeSets_updateExperimentProbeSets_nimbusExperiment_secondaryProbeSets {
  __typename: "NimbusProbeSetType";
  id: string;
  name: string;
}

export interface updateExperimentProbeSets_updateExperimentProbeSets_nimbusExperiment {
  __typename: "NimbusExperimentType";
  id: string;
  primaryProbeSets: (updateExperimentProbeSets_updateExperimentProbeSets_nimbusExperiment_primaryProbeSets | null)[] | null;
  secondaryProbeSets: (updateExperimentProbeSets_updateExperimentProbeSets_nimbusExperiment_secondaryProbeSets | null)[] | null;
}

export interface updateExperimentProbeSets_updateExperimentProbeSets {
  __typename: "UpdateExperimentProbeSets";
  clientMutationId: string | null;
  nimbusExperiment: updateExperimentProbeSets_updateExperimentProbeSets_nimbusExperiment | null;
  message: ObjectField | null;
  status: number | null;
}

export interface updateExperimentProbeSets {
  updateExperimentProbeSets: updateExperimentProbeSets_updateExperimentProbeSets | null;
}

export interface updateExperimentProbeSetsVariables {
  input: UpdateExperimentProbeSetsInput;
}
