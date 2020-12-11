/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentStatus, NimbusExperimentApplication, NimbusFeatureConfigApplication, NimbusExperimentChannel, NimbusExperimentFirefoxMinVersion, NimbusExperimentTargetingConfigSlug } from "./globalTypes";

// ====================================================
// GraphQL query operation: getExperiment
// ====================================================

export interface getExperiment_experimentBySlug_owner {
  __typename: "NimbusExperimentOwner";
  email: string;
}

export interface getExperiment_experimentBySlug_referenceBranch {
  __typename: "NimbusBranchType";
  name: string;
  slug: string;
  description: string;
  ratio: number;
  featureValue: string | null;
  featureEnabled: boolean;
}

export interface getExperiment_experimentBySlug_treatmentBranches {
  __typename: "NimbusBranchType";
  name: string;
  slug: string;
  description: string;
  ratio: number;
  featureValue: string | null;
  featureEnabled: boolean;
}

export interface getExperiment_experimentBySlug_featureConfig {
  __typename: "NimbusFeatureConfigType";
  id: string;
  slug: string;
  name: string;
  description: string | null;
  application: NimbusFeatureConfigApplication | null;
  ownerEmail: string | null;
  schema: string | null;
}

export interface getExperiment_experimentBySlug_primaryProbeSets {
  __typename: "NimbusProbeSetType";
  id: string;
  slug: string;
  name: string;
}

export interface getExperiment_experimentBySlug_secondaryProbeSets {
  __typename: "NimbusProbeSetType";
  id: string;
  slug: string;
  name: string;
}

export interface getExperiment_experimentBySlug_readyForReview {
  __typename: "NimbusReadyForReviewType";
  ready: boolean | null;
  message: ObjectField | null;
}

export interface getExperiment_experimentBySlug {
  __typename: "NimbusExperimentType";
  id: string;
  name: string;
  slug: string;
  status: NimbusExperimentStatus | null;
  monitoringDashboardUrl: string | null;
  hypothesis: string | null;
  application: NimbusExperimentApplication | null;
  publicDescription: string | null;
  owner: getExperiment_experimentBySlug_owner | null;
  referenceBranch: getExperiment_experimentBySlug_referenceBranch | null;
  treatmentBranches: (getExperiment_experimentBySlug_treatmentBranches | null)[] | null;
  featureConfig: getExperiment_experimentBySlug_featureConfig | null;
  primaryProbeSets: (getExperiment_experimentBySlug_primaryProbeSets | null)[] | null;
  secondaryProbeSets: (getExperiment_experimentBySlug_secondaryProbeSets | null)[] | null;
  channel: NimbusExperimentChannel | null;
  firefoxMinVersion: NimbusExperimentFirefoxMinVersion | null;
  targetingConfigSlug: NimbusExperimentTargetingConfigSlug | null;
  populationPercent: string | null;
  totalEnrolledClients: number;
  proposedEnrollment: number | null;
  proposedDuration: number | null;
  readyForReview: getExperiment_experimentBySlug_readyForReview | null;
  startDate: DateTime | null;
  endDate: DateTime | null;
}

export interface getExperiment {
  experimentBySlug: getExperiment_experimentBySlug | null;
}

export interface getExperimentVariables {
  slug: string;
}
