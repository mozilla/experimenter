/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentApplication, NimbusExperimentFirefoxMinVersion, NimbusExperimentStatus, NimbusExperimentPublishStatus } from "./globalTypes";

// ====================================================
// GraphQL query operation: getAllExperiments
// ====================================================

export interface getAllExperiments_experiments_owner {
  username: string;
}

export interface getAllExperiments_experiments_featureConfig {
  id: number | null;
  slug: string;
  name: string;
  description: string | null;
  application: NimbusExperimentApplication | null;
  ownerEmail: string | null;
  schema: string | null;
}

export interface getAllExperiments_experiments {
  isArchived: boolean | null;
  name: string;
  owner: getAllExperiments_experiments_owner;
  featureConfig: getAllExperiments_experiments_featureConfig | null;
  slug: string;
  application: NimbusExperimentApplication | null;
  firefoxMinVersion: NimbusExperimentFirefoxMinVersion | null;
  startDate: DateTime | null;
  isEnrollmentPausePending: boolean | null;
  isEnrollmentPaused: boolean | null;
  proposedDuration: number;
  proposedEnrollment: number;
  computedEndDate: DateTime | null;
  status: NimbusExperimentStatus | null;
  statusNext: NimbusExperimentStatus | null;
  publishStatus: NimbusExperimentPublishStatus | null;
  monitoringDashboardUrl: string | null;
  resultsReady: boolean | null;
}

export interface getAllExperiments {
  experiments: (getAllExperiments_experiments | null)[] | null;
}
