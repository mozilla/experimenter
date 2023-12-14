/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentApplicationEnum, NimbusExperimentFirefoxVersionEnum, NimbusExperimentStatusEnum, NimbusExperimentPublishStatusEnum, NimbusExperimentQAStatusEnum, NimbusExperimentChannelEnum } from "./globalTypes";

// ====================================================
// GraphQL query operation: getAllExperiments
// ====================================================

export interface getAllExperiments_experiments_owner {
  /**
   * Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.
   */
  username: string;
}

export interface getAllExperiments_experiments_featureConfigs {
  id: number | null;
  slug: string;
  name: string;
  description: string | null;
  application: NimbusExperimentApplicationEnum | null;
  ownerEmail: string | null;
}

export interface getAllExperiments_experiments_targetingConfig {
  label: string | null;
  value: string | null;
  description: string | null;
  applicationValues: (string | null)[] | null;
  stickyRequired: boolean | null;
  isFirstRunRequired: boolean | null;
}

export interface getAllExperiments_experiments_projects {
  id: string | null;
  name: string | null;
}

export interface getAllExperiments_experiments {
  isArchived: boolean | null;
  isRollout: boolean | null;
  name: string;
  owner: getAllExperiments_experiments_owner;
  featureConfigs: getAllExperiments_experiments_featureConfigs[] | null;
  targetingConfig: (getAllExperiments_experiments_targetingConfig | null)[] | null;
  slug: string;
  application: NimbusExperimentApplicationEnum | null;
  firefoxMinVersion: NimbusExperimentFirefoxVersionEnum | null;
  firefoxMaxVersion: NimbusExperimentFirefoxVersionEnum | null;
  startDate: DateTime | null;
  isRolloutDirty: boolean;
  isEnrollmentPausePending: boolean | null;
  isEnrollmentPaused: boolean | null;
  proposedDuration: number;
  proposedEnrollment: number;
  proposedReleaseDate: string | null;
  computedEndDate: DateTime | null;
  computedEnrollmentEndDate: DateTime | null;
  status: NimbusExperimentStatusEnum | null;
  statusNext: NimbusExperimentStatusEnum | null;
  publishStatus: NimbusExperimentPublishStatusEnum | null;
  qaStatus: NimbusExperimentQAStatusEnum | null;
  monitoringDashboardUrl: string | null;
  rolloutMonitoringDashboardUrl: string | null;
  resultsExpectedDate: DateTime | null;
  resultsReady: boolean | null;
  showResultsUrl: boolean | null;
  channel: NimbusExperimentChannelEnum | null;
  populationPercent: string | null;
  projects: (getAllExperiments_experiments_projects | null)[] | null;
  hypothesis: string | null;
  takeawaysMetricGain: boolean;
  takeawaysQbrLearning: boolean;
}

export interface getAllExperiments {
  /**
   * List Nimbus Experiments.
   */
  experiments: (getAllExperiments_experiments | null)[] | null;
}
