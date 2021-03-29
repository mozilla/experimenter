/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentStatus, NimbusExperimentPublishStatus, NimbusExperimentApplication, NimbusFeatureConfigApplication, NimbusExperimentChannel, NimbusExperimentFirefoxMinVersion, NimbusExperimentTargetingConfigSlug, NimbusDocumentationLinkTitle } from "./globalTypes";

// ====================================================
// GraphQL query operation: getExperiment
// ====================================================

export interface getExperiment_experimentBySlug_owner {
  email: string;
}

export interface getExperiment_experimentBySlug_referenceBranch {
  name: string;
  slug: string;
  description: string;
  ratio: number;
  featureValue: string | null;
  featureEnabled: boolean;
}

export interface getExperiment_experimentBySlug_treatmentBranches {
  name: string;
  slug: string;
  description: string;
  ratio: number;
  featureValue: string | null;
  featureEnabled: boolean;
}

export interface getExperiment_experimentBySlug_featureConfig {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  application: NimbusFeatureConfigApplication | null;
  ownerEmail: string | null;
  schema: string | null;
}

export interface getExperiment_experimentBySlug_readyForReview {
  ready: boolean | null;
  message: ObjectField | null;
}

export interface getExperiment_experimentBySlug_documentationLinks {
  title: NimbusDocumentationLinkTitle;
  link: string;
}

export interface getExperiment_experimentBySlug {
  id: number | null;
  name: string;
  slug: string;
  status: NimbusExperimentStatus | null;
  publishStatus: NimbusExperimentPublishStatus | null;
  monitoringDashboardUrl: string | null;
  isEndRequested: boolean;
  hypothesis: string;
  application: NimbusExperimentApplication | null;
  publicDescription: string;
  owner: getExperiment_experimentBySlug_owner;
  referenceBranch: getExperiment_experimentBySlug_referenceBranch | null;
  treatmentBranches: (getExperiment_experimentBySlug_treatmentBranches | null)[] | null;
  featureConfig: getExperiment_experimentBySlug_featureConfig | null;
  primaryOutcomes: (string | null)[] | null;
  secondaryOutcomes: (string | null)[] | null;
  channel: NimbusExperimentChannel | null;
  firefoxMinVersion: NimbusExperimentFirefoxMinVersion | null;
  targetingConfigSlug: NimbusExperimentTargetingConfigSlug | null;
  jexlTargetingExpression: string | null;
  populationPercent: string | null;
  totalEnrolledClients: number;
  proposedEnrollment: number;
  proposedDuration: number;
  readyForReview: getExperiment_experimentBySlug_readyForReview | null;
  startDate: DateTime | null;
  computedEndDate: DateTime | null;
  riskMitigationLink: string;
  documentationLinks: getExperiment_experimentBySlug_documentationLinks[] | null;
  isEnrollmentPaused: boolean | null;
  enrollmentEndDate: DateTime | null;
}

export interface getExperiment {
  experimentBySlug: getExperiment_experimentBySlug | null;
}

export interface getExperimentVariables {
  slug: string;
}
