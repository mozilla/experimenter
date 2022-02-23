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
  username: string;
}

export interface getConfig_nimbusConfig_targetingConfigs {
  label: string | null;
  value: string | null;
  applicationValues: (string | null)[] | null;
}

export interface getConfig_nimbusConfig_documentationLink {
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_locales {
  id: number | null;
  name: string | null;
}

export interface getConfig_nimbusConfig_countries {
  id: number | null;
  name: string | null;
}

export interface getConfig_nimbusConfig {
  applications: (getConfig_nimbusConfig_applications | null)[] | null;
  channels: (getConfig_nimbusConfig_channels | null)[] | null;
  conclusionRecommendations: (getConfig_nimbusConfig_conclusionRecommendations | null)[] | null;
  applicationConfigs: (getConfig_nimbusConfig_applicationConfigs | null)[] | null;
  allFeatureConfigs: (getConfig_nimbusConfig_allFeatureConfigs | null)[] | null;
  firefoxVersions: (getConfig_nimbusConfig_firefoxVersions | null)[] | null;
  outcomes: (getConfig_nimbusConfig_outcomes | null)[] | null;
  owners: (getConfig_nimbusConfig_owners | null)[] | null;
  targetingConfigs: (getConfig_nimbusConfig_targetingConfigs | null)[] | null;
  hypothesisDefault: string | null;
  documentationLink: (getConfig_nimbusConfig_documentationLink | null)[] | null;
  maxPrimaryOutcomes: number | null;
  locales: (getConfig_nimbusConfig_locales | null)[] | null;
  countries: (getConfig_nimbusConfig_countries | null)[] | null;
}

export interface getConfig {
  nimbusConfig: getConfig_nimbusConfig | null;
}
