/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { UpdateExperimentAudienceInput, NimbusExperimentChannel, NimbusExperimentFirefoxMinVersion, NimbusExperimentTargetingConfigSlug } from "./globalTypes";

// ====================================================
// GraphQL mutation operation: updateExperimentAudience
// ====================================================

export interface updateExperimentAudience_updateExperimentAudience_nimbusExperiment {
  __typename: "NimbusExperimentType";
  id: string;
  totalEnrolledClients: number;
  channels: (NimbusExperimentChannel | null)[] | null;
  firefoxMinVersion: NimbusExperimentFirefoxMinVersion | null;
  populationPercent: number | null;
  proposedDuration: number | null;
  proposedEnrollment: number | null;
  targetingConfigSlug: NimbusExperimentTargetingConfigSlug | null;
}

export interface updateExperimentAudience_updateExperimentAudience {
  __typename: "UpdateExperimentAudience";
  clientMutationId: string | null;
  message: ObjectField | null;
  status: number | null;
  nimbusExperiment: updateExperimentAudience_updateExperimentAudience_nimbusExperiment | null;
}

export interface updateExperimentAudience {
  updateExperimentAudience: updateExperimentAudience_updateExperimentAudience | null;
}

export interface updateExperimentAudienceVariables {
  input: UpdateExperimentAudienceInput;
}
