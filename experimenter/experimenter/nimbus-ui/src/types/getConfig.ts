/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusExperimentApplicationEnum } from "./globalTypes";

// ====================================================
// GraphQL query operation: getConfig
// ====================================================

export interface getConfig_nimbusConfig_applications {
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_channels {
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_conclusionRecommendations {
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_applicationConfigs_channels {
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_applicationConfigs {
  application: NimbusExperimentApplicationEnum | null;
  channels: (getConfig_nimbusConfig_applicationConfigs_channels | null)[] | null;
}

export interface getConfig_nimbusConfig_allFeatureConfigs {
  id: number | null;
  name: string;
  slug: string;
  description: string | null;
  application: NimbusExperimentApplicationEnum | null;
  ownerEmail: string | null;
  schema: string | null;
  setsPrefs: boolean | null;
  enabled: boolean;
}

export interface getConfig_nimbusConfig_firefoxVersions {
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_outcomes_metrics {
  slug: string | null;
  friendlyName: string | null;
  description: string | null;
}

export interface getConfig_nimbusConfig_outcomes {
  friendlyName: string | null;
  slug: string | null;
  application: NimbusExperimentApplicationEnum | null;
  description: string | null;
  isDefault: boolean | null;
  metrics: (getConfig_nimbusConfig_outcomes_metrics | null)[] | null;
}

export interface getConfig_nimbusConfig_owners {
  /**
   * Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.
   */
  username: string;
}

export interface getConfig_nimbusConfig_targetingConfigs {
  label: string | null;
  value: string | null;
  description: string | null;
  applicationValues: (string | null)[] | null;
  stickyRequired: boolean | null;
  isFirstRunRequired: boolean | null;
}

export interface getConfig_nimbusConfig_documentationLink {
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_locales {
  id: string;
  name: string;
  code: string;
}

export interface getConfig_nimbusConfig_countries {
  id: string;
  name: string;
  code: string;
}

export interface getConfig_nimbusConfig_languages {
  id: string;
  name: string;
  code: string;
}

export interface getConfig_nimbusConfig_projects {
  id: string | null;
  name: string | null;
}

export interface getConfig_nimbusConfig_types {
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_statusUpdateExemptFields {
  all: (string | null)[] | null;
  experiments: (string | null)[] | null;
  rollouts: (string | null)[] | null;
}

export interface getConfig_nimbusConfig_takeaways {
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_qaStatus {
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig {
  applications: (getConfig_nimbusConfig_applications | null)[] | null;
  channels: (getConfig_nimbusConfig_channels | null)[] | null;
  conclusionRecommendations: (getConfig_nimbusConfig_conclusionRecommendations | null)[] | null;
  applicationConfigs: (getConfig_nimbusConfig_applicationConfigs | null)[] | null;
  allFeatureConfigs: getConfig_nimbusConfig_allFeatureConfigs[] | null;
  firefoxVersions: (getConfig_nimbusConfig_firefoxVersions | null)[] | null;
  outcomes: (getConfig_nimbusConfig_outcomes | null)[] | null;
  owners: (getConfig_nimbusConfig_owners | null)[] | null;
  targetingConfigs: (getConfig_nimbusConfig_targetingConfigs | null)[] | null;
  hypothesisDefault: string | null;
  documentationLink: (getConfig_nimbusConfig_documentationLink | null)[] | null;
  maxPrimaryOutcomes: number | null;
  locales: (getConfig_nimbusConfig_locales | null)[] | null;
  countries: (getConfig_nimbusConfig_countries | null)[] | null;
  languages: (getConfig_nimbusConfig_languages | null)[] | null;
  projects: (getConfig_nimbusConfig_projects | null)[] | null;
  types: (getConfig_nimbusConfig_types | null)[] | null;
  statusUpdateExemptFields: (getConfig_nimbusConfig_statusUpdateExemptFields | null)[] | null;
  populationSizingData: string | null;
  takeaways: (getConfig_nimbusConfig_takeaways | null)[] | null;
  qaStatus: (getConfig_nimbusConfig_qaStatus | null)[] | null;
}

export interface getConfig {
  /**
   * Nimbus Configuration Data for front-end usage.
   */
  nimbusConfig: getConfig_nimbusConfig | null;
}
