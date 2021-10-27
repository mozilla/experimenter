/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentStatus, NimbusExperimentPublishStatus, NimbusExperimentApplication, NimbusExperimentConclusionRecommendation, NimbusExperimentChannel, NimbusExperimentFirefoxMinVersion, NimbusDocumentationLinkTitle, NimbusChangeLogOldStatus, NimbusChangeLogOldStatusNext } from "./globalTypes";

// ====================================================
// GraphQL query operation: getExperiment
// ====================================================

export interface getExperiment_experimentBySlug_owner {
  email: string;
}

export interface getExperiment_experimentBySlug_parent {
  name: string;
  slug: string;
}

export interface getExperiment_experimentBySlug_referenceBranch_screenshots {
  id: number | null;
  description: string | null;
  image: string | null;
}

export interface getExperiment_experimentBySlug_referenceBranch {
  id: number | null;
  name: string;
  slug: string;
  description: string;
  ratio: number;
  featureValue: string | null;
  screenshots: getExperiment_experimentBySlug_referenceBranch_screenshots[] | null;
}

export interface getExperiment_experimentBySlug_treatmentBranches_screenshots {
  id: number | null;
  description: string | null;
  image: string | null;
}

export interface getExperiment_experimentBySlug_treatmentBranches {
  id: number | null;
  name: string;
  slug: string;
  description: string;
  ratio: number;
  featureValue: string | null;
  screenshots: getExperiment_experimentBySlug_treatmentBranches_screenshots[] | null;
}

export interface getExperiment_experimentBySlug_featureConfig {
  id: number | null;
  slug: string;
  name: string;
  description: string | null;
  application: NimbusExperimentApplication | null;
  ownerEmail: string | null;
  schema: string | null;
}

export interface getExperiment_experimentBySlug_readyForReview {
  ready: boolean | null;
  message: ObjectField | null;
}

export interface getExperiment_experimentBySlug_signoffRecommendations {
  qaSignoff: boolean | null;
  vpSignoff: boolean | null;
  legalSignoff: boolean | null;
}

export interface getExperiment_experimentBySlug_documentationLinks {
  title: NimbusDocumentationLinkTitle;
  link: string;
}

export interface getExperiment_experimentBySlug_reviewRequest_changedBy {
  email: string;
}

export interface getExperiment_experimentBySlug_reviewRequest {
  changedOn: DateTime;
  changedBy: getExperiment_experimentBySlug_reviewRequest_changedBy;
}

export interface getExperiment_experimentBySlug_rejection_changedBy {
  email: string;
}

export interface getExperiment_experimentBySlug_rejection {
  message: string | null;
  oldStatus: NimbusChangeLogOldStatus | null;
  oldStatusNext: NimbusChangeLogOldStatusNext | null;
  changedOn: DateTime;
  changedBy: getExperiment_experimentBySlug_rejection_changedBy;
}

export interface getExperiment_experimentBySlug_timeout_changedBy {
  email: string;
}

export interface getExperiment_experimentBySlug_timeout {
  changedOn: DateTime;
  changedBy: getExperiment_experimentBySlug_timeout_changedBy;
}

export interface getExperiment_experimentBySlug_locales {
  id: number | null;
  name: string | null;
}

export interface getExperiment_experimentBySlug_countries {
  id: number | null;
  name: string | null;
}

export interface getExperiment_experimentBySlug {
  id: number | null;
  isArchived: boolean | null;
  canEdit: boolean | null;
  canArchive: boolean | null;
  name: string;
  slug: string;
  status: NimbusExperimentStatus | null;
  statusNext: NimbusExperimentStatus | null;
  publishStatus: NimbusExperimentPublishStatus | null;
  monitoringDashboardUrl: string | null;
  resultsReady: boolean | null;
  hypothesis: string;
  application: NimbusExperimentApplication | null;
  publicDescription: string;
  conclusionRecommendation: NimbusExperimentConclusionRecommendation | null;
  takeawaysSummary: string | null;
  owner: getExperiment_experimentBySlug_owner;
  parent: getExperiment_experimentBySlug_parent | null;
  referenceBranch: getExperiment_experimentBySlug_referenceBranch | null;
  treatmentBranches: (getExperiment_experimentBySlug_treatmentBranches | null)[] | null;
  featureConfig: getExperiment_experimentBySlug_featureConfig | null;
  primaryOutcomes: (string | null)[] | null;
  secondaryOutcomes: (string | null)[] | null;
  channel: NimbusExperimentChannel | null;
  firefoxMinVersion: NimbusExperimentFirefoxMinVersion | null;
  targetingConfigSlug: string | null;
  jexlTargetingExpression: string | null;
  populationPercent: string | null;
  totalEnrolledClients: number;
  proposedEnrollment: number;
  proposedDuration: number;
  readyForReview: getExperiment_experimentBySlug_readyForReview | null;
  startDate: DateTime | null;
  computedEndDate: DateTime | null;
  computedEnrollmentDays: number | null;
  computedDurationDays: number | null;
  riskMitigationLink: string;
  riskRevenue: boolean | null;
  riskBrand: boolean | null;
  riskPartnerRelated: boolean | null;
  signoffRecommendations: getExperiment_experimentBySlug_signoffRecommendations | null;
  documentationLinks: getExperiment_experimentBySlug_documentationLinks[] | null;
  isEnrollmentPausePending: boolean | null;
  isEnrollmentPaused: boolean | null;
  enrollmentEndDate: DateTime | null;
  canReview: boolean | null;
  reviewRequest: getExperiment_experimentBySlug_reviewRequest | null;
  rejection: getExperiment_experimentBySlug_rejection | null;
  timeout: getExperiment_experimentBySlug_timeout | null;
  recipeJson: string | null;
  reviewUrl: string | null;
  locales: getExperiment_experimentBySlug_locales[];
  countries: getExperiment_experimentBySlug_countries[];
}

export interface getExperiment {
  experimentBySlug: getExperiment_experimentBySlug | null;
}

export interface getExperimentVariables {
  slug: string;
}
