/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExperimentInput } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: updateExperimentOverview
// ====================================================

export interface updateExperimentOverview_updateExperiment_nimbusExperiment {
  __typename: "NimbusExperimentType";
  name: string;
  hypothesis: string;
  publicDescription: string;
}

export interface updateExperimentOverview_updateExperiment {
  __typename: "UpdateExperiment";
  clientMutationId: string | null;
  message: ObjectField | null;
  status: number | null;
  nimbusExperiment: updateExperimentOverview_updateExperiment_nimbusExperiment | null;
}

export interface updateExperimentOverview {
  updateExperiment: updateExperimentOverview_updateExperiment | null;
}

export interface updateExperimentOverviewVariables {
  input: ExperimentInput;
}
