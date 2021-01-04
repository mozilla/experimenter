/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ExperimentInput, NimbusExperimentChannel, NimbusExperimentFirefoxMinVersion, NimbusExperimentTargetingConfigSlug } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: updateExperimentAudience
// ====================================================

export interface updateExperimentAudience_updateExperiment_nimbusExperiment {
  __typename: "NimbusExperimentType";
  id: number | null;
  totalEnrolledClients: number;
  channel: NimbusExperimentChannel | null;
  firefoxMinVersion: NimbusExperimentFirefoxMinVersion | null;
  populationPercent: string | null;
  proposedDuration: number | null;
  proposedEnrollment: number | null;
  targetingConfigSlug: NimbusExperimentTargetingConfigSlug | null;
}

export interface updateExperimentAudience_updateExperiment {
  __typename: "UpdateExperiment";
  clientMutationId: string | null;
  message: ObjectField | null;
  status: number | null;
  nimbusExperiment: updateExperimentAudience_updateExperiment_nimbusExperiment | null;
}

export interface updateExperimentAudience {
  updateExperiment: updateExperimentAudience_updateExperiment | null;
}

export interface updateExperimentAudienceVariables {
  input: ExperimentInput;
}
