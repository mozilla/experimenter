/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentStatus } from "./globalTypes";

// ====================================================
// GraphQL query operation: getAllExperiments
// ====================================================

export interface getAllExperiments_experiments_owner {
  __typename: "NimbusExperimentOwner";
  username: string;
}

export interface getAllExperiments_experiments_featureConfig {
  __typename: "NimbusFeatureConfigType";
  slug: string;
  name: string;
}

export interface getAllExperiments_experiments {
  __typename: "NimbusExperimentType";
  name: string;
  owner: getAllExperiments_experiments_owner | null;
  slug: string;
  startDate: DateTime | null;
  proposedDuration: number | null;
  proposedEnrollment: number | null;
  endDate: DateTime | null;
  status: NimbusExperimentStatus | null;
  monitoringDashboardUrl: string | null;
  featureConfig: getAllExperiments_experiments_featureConfig | null;
}

export interface getAllExperiments {
  experiments: (getAllExperiments_experiments | null)[] | null;
}
