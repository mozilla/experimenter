/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { UpdateExperimentInput, NimbusExperimentApplication } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: updateExperimentOverview
// ====================================================

export interface updateExperimentOverview_updateExperimentOverview_nimbusExperiment {
  __typename: "NimbusExperimentType";
  name: string;
  hypothesis: string | null;
  application: NimbusExperimentApplication | null;
  publicDescription: string | null;
}

export interface updateExperimentOverview_updateExperimentOverview {
  __typename: "UpdateExperimentOverview";
  clientMutationId: string | null;
  message: any | null;
  status: number | null;
  nimbusExperiment: updateExperimentOverview_updateExperimentOverview_nimbusExperiment | null;
}

export interface updateExperimentOverview {
  /**
   * Update a Nimbus Experiment.
   */
  updateExperimentOverview: updateExperimentOverview_updateExperimentOverview | null;
}

export interface updateExperimentOverviewVariables {
  input: UpdateExperimentInput;
}
