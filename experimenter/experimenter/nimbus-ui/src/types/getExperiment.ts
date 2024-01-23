/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentStatusEnum, NimbusExperimentPublishStatusEnum, NimbusExperimentApplicationEnum, NimbusExperimentConclusionRecommendationEnum, NimbusExperimentChannelEnum, NimbusExperimentFirefoxVersionEnum, NimbusExperimentDocumentationLinkEnum, NimbusExperimentQAStatusEnum } from "./globalTypes";

// ====================================================
// GraphQL query operation: getExperiment
// ====================================================

export interface getExperiment_experimentBySlug_owner {
  email: string;
}

export interface getExperiment_experimentBySlug_subscribers {
  email: string;
}

export interface getExperiment_experimentBySlug_parent {
  name: string;
  slug: string;
}

export interface getExperiment_experimentBySlug_referenceBranch_featureValues_featureConfig {
  id: number | null;
}

export interface getExperiment_experimentBySlug_referenceBranch_featureValues {
  featureConfig: getExperiment_experimentBySlug_referenceBranch_featureValues_featureConfig | null;
  value: string | null;
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
  featureValues: (getExperiment_experimentBySlug_referenceBranch_featureValues | null)[] | null;
  screenshots: getExperiment_experimentBySlug_referenceBranch_screenshots[] | null;
}

export interface getExperiment_experimentBySlug_treatmentBranches_featureValues_featureConfig {
  id: number | null;
}

export interface getExperiment_experimentBySlug_treatmentBranches_featureValues {
  featureConfig: getExperiment_experimentBySlug_treatmentBranches_featureValues_featureConfig | null;
  value: string | null;
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
  featureValues: (getExperiment_experimentBySlug_treatmentBranches_featureValues | null)[] | null;
  screenshots: getExperiment_experimentBySlug_treatmentBranches_screenshots[] | null;
}

export interface getExperiment_experimentBySlug_featureConfigs {
  id: number | null;
  slug: string;
  name: string;
  description: string | null;
  application: NimbusExperimentApplicationEnum | null;
  ownerEmail: string | null;
  schema: string | null;
  enabled: boolean;
}

export interface getExperiment_experimentBySlug_targetingConfig {
  label: string | null;
  value: string | null;
  applicationValues: (string | null)[] | null;
  description: string | null;
  stickyRequired: boolean | null;
  isFirstRunRequired: boolean | null;
}

export interface getExperiment_experimentBySlug_excludedExperimentsBranches_excludedExperiment_referenceBranch {
  slug: string;
}

export interface getExperiment_experimentBySlug_excludedExperimentsBranches_excludedExperiment_treatmentBranches {
  slug: string;
}

export interface getExperiment_experimentBySlug_excludedExperimentsBranches_excludedExperiment {
  id: number;
  slug: string;
  name: string;
  publicDescription: string | null;
  referenceBranch: getExperiment_experimentBySlug_excludedExperimentsBranches_excludedExperiment_referenceBranch | null;
  treatmentBranches: (getExperiment_experimentBySlug_excludedExperimentsBranches_excludedExperiment_treatmentBranches | null)[] | null;
}

export interface getExperiment_experimentBySlug_excludedExperimentsBranches {
  excludedExperiment: getExperiment_experimentBySlug_excludedExperimentsBranches_excludedExperiment;
  branchSlug: string | null;
}

export interface getExperiment_experimentBySlug_requiredExperimentsBranches_requiredExperiment_referenceBranch {
  slug: string;
}

export interface getExperiment_experimentBySlug_requiredExperimentsBranches_requiredExperiment_treatmentBranches {
  slug: string;
}

export interface getExperiment_experimentBySlug_requiredExperimentsBranches_requiredExperiment {
  id: number;
  slug: string;
  name: string;
  publicDescription: string | null;
  referenceBranch: getExperiment_experimentBySlug_requiredExperimentsBranches_requiredExperiment_referenceBranch | null;
  treatmentBranches: (getExperiment_experimentBySlug_requiredExperimentsBranches_requiredExperiment_treatmentBranches | null)[] | null;
}

export interface getExperiment_experimentBySlug_requiredExperimentsBranches {
  requiredExperiment: getExperiment_experimentBySlug_requiredExperimentsBranches_requiredExperiment;
  branchSlug: string | null;
}

export interface getExperiment_experimentBySlug_readyForReview {
  ready: boolean | null;
  message: ObjectField | null;
  warnings: ObjectField | null;
}

export interface getExperiment_experimentBySlug_signoffRecommendations {
  qaSignoff: boolean | null;
  vpSignoff: boolean | null;
  legalSignoff: boolean | null;
}

export interface getExperiment_experimentBySlug_documentationLinks {
  title: NimbusExperimentDocumentationLinkEnum | null;
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
  oldStatus: NimbusExperimentStatusEnum | null;
  oldStatusNext: NimbusExperimentStatusEnum | null;
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
  id: string;
  name: string;
  code: string;
}

export interface getExperiment_experimentBySlug_countries {
  id: string;
  name: string;
  code: string;
}

export interface getExperiment_experimentBySlug_languages {
  id: string;
  name: string;
  code: string;
}

export interface getExperiment_experimentBySlug_projects {
  id: string | null;
  name: string | null;
}

export interface getExperiment_experimentBySlug {
  id: number;
  isRollout: boolean | null;
  isArchived: boolean | null;
  canEdit: boolean | null;
  canArchive: boolean | null;
  name: string;
  slug: string;
  status: NimbusExperimentStatusEnum | null;
  statusNext: NimbusExperimentStatusEnum | null;
  publishStatus: NimbusExperimentPublishStatusEnum | null;
  monitoringDashboardUrl: string | null;
  rolloutMonitoringDashboardUrl: string | null;
  resultsExpectedDate: DateTime | null;
  resultsReady: boolean | null;
  showResultsUrl: boolean | null;
  hypothesis: string | null;
  application: NimbusExperimentApplicationEnum | null;
  publicDescription: string | null;
  conclusionRecommendation: NimbusExperimentConclusionRecommendationEnum | null;
  takeawaysGainAmount: string | null;
  takeawaysMetricGain: boolean;
  takeawaysQbrLearning: boolean;
  takeawaysSummary: string | null;
  owner: getExperiment_experimentBySlug_owner;
  subscribers: getExperiment_experimentBySlug_subscribers[];
  parent: getExperiment_experimentBySlug_parent | null;
  warnFeatureSchema: boolean | null;
  referenceBranch: getExperiment_experimentBySlug_referenceBranch | null;
  treatmentBranches: (getExperiment_experimentBySlug_treatmentBranches | null)[] | null;
  preventPrefConflicts: boolean | null;
  featureConfigs: getExperiment_experimentBySlug_featureConfigs[] | null;
  primaryOutcomes: (string | null)[] | null;
  secondaryOutcomes: (string | null)[] | null;
  channel: NimbusExperimentChannelEnum | null;
  firefoxMinVersion: NimbusExperimentFirefoxVersionEnum | null;
  firefoxMaxVersion: NimbusExperimentFirefoxVersionEnum | null;
  targetingConfigSlug: string | null;
  targetingConfig: (getExperiment_experimentBySlug_targetingConfig | null)[] | null;
  isSticky: boolean | null;
  isFirstRun: boolean;
  isWeb: boolean;
  excludedExperimentsBranches: getExperiment_experimentBySlug_excludedExperimentsBranches[];
  requiredExperimentsBranches: getExperiment_experimentBySlug_requiredExperimentsBranches[];
  jexlTargetingExpression: string | null;
  populationPercent: string | null;
  totalEnrolledClients: number;
  proposedEnrollment: number;
  proposedDuration: number;
  proposedReleaseDate: string | null;
  readyForReview: getExperiment_experimentBySlug_readyForReview | null;
  startDate: DateTime | null;
  computedDurationDays: number | null;
  computedEndDate: DateTime | null;
  computedEnrollmentDays: number | null;
  computedEnrollmentEndDate: DateTime | null;
  riskMitigationLink: string | null;
  riskRevenue: boolean | null;
  riskBrand: boolean | null;
  riskPartnerRelated: boolean | null;
  isLocalized: boolean | null;
  localizations: string | null;
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
  languages: getExperiment_experimentBySlug_languages[];
  projects: (getExperiment_experimentBySlug_projects | null)[] | null;
  isRolloutDirty: boolean;
  qaComment: string | null;
  qaStatus: NimbusExperimentQAStatusEnum | null;
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
