/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentStatus, NimbusExperimentPublishStatus } from "./globalTypes";

// ====================================================
// GraphQL query operation: getAllExperiments
// ====================================================

export interface getAllExperiments_experiments_owner {
  username: string;
}

export interface getAllExperiments_experiments_featureConfig {
  slug: string;
  name: string;
}

export interface getAllExperiments_experiments {
  name: string;
  owner: getAllExperiments_experiments_owner;
  slug: string;
  startDate: DateTime | null;
  proposedDuration: number;
  proposedEnrollment: number;
  computedEndDate: DateTime | null;
  status: NimbusExperimentStatus | null;
  statusNext: NimbusExperimentStatus | null;
  publishStatus: NimbusExperimentPublishStatus | null;
  monitoringDashboardUrl: string | null;
  resultsReady: boolean | null;
  featureConfig: getAllExperiments_experiments_featureConfig | null;
}

export interface getAllExperiments {
  experiments: (getAllExperiments_experiments | null)[] | null;
}
