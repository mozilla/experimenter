/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentStatus, NimbusExperimentApplication, NimbusFeatureConfigApplication, NimbusExperimentChannel, NimbusExperimentFirefoxMinVersion, NimbusExperimentTargetingConfigSlug } from "./globalTypes";

// ====================================================
// GraphQL query operation: getExperiment
// ====================================================

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
  slug: string;
  name: string;
  description: string | null;
  application: NimbusFeatureConfigApplication | null;
  ownerEmail: string | null;
  schema: string | null;
}

export interface getExperiment_experimentBySlug_primaryProbeSets {
  __typename: "NimbusProbeSetType";
  slug: string;
  name: string;
}

export interface getExperiment_experimentBySlug_secondaryProbeSets {
  __typename: "NimbusProbeSetType";
  slug: string;
  name: string;
}

export interface getExperiment_experimentBySlug {
  __typename: "NimbusExperimentType";
  id: string;
  name: string;
  slug: string;
  status: NimbusExperimentStatus | null;
  hypothesis: string | null;
  application: NimbusExperimentApplication | null;
  publicDescription: string | null;
  referenceBranch: getExperiment_experimentBySlug_referenceBranch | null;
  treatmentBranches: (getExperiment_experimentBySlug_treatmentBranches | null)[] | null;
  featureConfig: getExperiment_experimentBySlug_featureConfig | null;
  primaryProbeSets: (getExperiment_experimentBySlug_primaryProbeSets | null)[] | null;
  secondaryProbeSets: (getExperiment_experimentBySlug_secondaryProbeSets | null)[] | null;
  channels: (NimbusExperimentChannel | null)[] | null;
  firefoxMinVersion: NimbusExperimentFirefoxMinVersion | null;
  targetingConfigSlug: NimbusExperimentTargetingConfigSlug | null;
  populationPercent: number | null;
  totalEnrolledClients: number;
  proposedEnrollment: number | null;
}

export interface getExperiment {
  /**
   * Retrieve a Nimbus experiment by its slug.
   */
  experimentBySlug: getExperiment_experimentBySlug | null;
}

export interface getExperimentVariables {
  slug: string;
}
