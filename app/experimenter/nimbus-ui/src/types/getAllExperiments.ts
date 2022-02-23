/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentApplicationEnum, NimbusExperimentFirefoxVersionEnum, NimbusExperimentStatusEnum, NimbusExperimentPublishStatusEnum } from "./globalTypes";

// ====================================================
// GraphQL query operation: getAllExperiments
// ====================================================

export interface getAllExperiments_experiments_owner {
  username: string;
}

export interface getAllExperiments_experiments_featureConfigs {
  id: number | null;
  slug: string;
  name: string;
  description: string | null;
  application: NimbusExperimentApplicationEnum | null;
  ownerEmail: string | null;
  schema: string | null;
}

export interface getAllExperiments_experiments_featureConfig {
  slug: string;
  name: string;
}

export interface getAllExperiments_experiments {
  isArchived: boolean | null;
  name: string;
  owner: getAllExperiments_experiments_owner;
  featureConfigs: (getAllExperiments_experiments_featureConfigs | null)[] | null;
  slug: string;
  application: NimbusExperimentApplicationEnum | null;
  firefoxMinVersion: NimbusExperimentFirefoxVersionEnum | null;
  firefoxMaxVersion: NimbusExperimentFirefoxVersionEnum | null;
  startDate: DateTime | null;
  isEnrollmentPausePending: boolean | null;
  isEnrollmentPaused: boolean | null;
  proposedDuration: number;
  proposedEnrollment: number;
  computedEndDate: DateTime | null;
  status: NimbusExperimentStatusEnum | null;
  statusNext: NimbusExperimentStatusEnum | null;
  publishStatus: NimbusExperimentPublishStatusEnum | null;
  monitoringDashboardUrl: string | null;
  resultsReady: boolean | null;
  featureConfig: getAllExperiments_experiments_featureConfig | null;
}

export interface getAllExperiments {
  experiments: (getAllExperiments_experiments | null)[] | null;
}
