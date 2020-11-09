/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { NimbusFeatureConfigApplication, NimbusProbeKind } from "./globalTypes";

// ====================================================
// GraphQL query operation: getConfig
// ====================================================

export interface getConfig_nimbusConfig_application {
  __typename: "NimbusLabelValueType";
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_channels {
  __typename: "NimbusLabelValueType";
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_featureConfig {
  __typename: "NimbusFeatureConfigType";
  id: string;
  name: string;
  slug: string;
  description: string | null;
  application: NimbusFeatureConfigApplication | null;
  ownerEmail: string | null;
  schema: string | null;
}

export interface getConfig_nimbusConfig_firefoxMinVersion {
  __typename: "NimbusLabelValueType";
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig_probeSets_probes {
  __typename: "NimbusProbeType";
  id: string;
  kind: NimbusProbeKind;
  name: string;
  eventCategory: string;
  eventMethod: string | null;
  eventObject: string | null;
  eventValue: string | null;
}

export interface getConfig_nimbusConfig_probeSets {
  __typename: "NimbusProbeSetType";
  id: string;
  name: string;
  slug: string;
  probes: getConfig_nimbusConfig_probeSets_probes[];
}

export interface getConfig_nimbusConfig_targetingConfigSlug {
  __typename: "NimbusLabelValueType";
  label: string | null;
  value: string | null;
}

export interface getConfig_nimbusConfig {
  __typename: "NimbusConfigurationType";
  application: (getConfig_nimbusConfig_application | null)[] | null;
  channels: (getConfig_nimbusConfig_channels | null)[] | null;
  featureConfig: (getConfig_nimbusConfig_featureConfig | null)[] | null;
  firefoxMinVersion: (getConfig_nimbusConfig_firefoxMinVersion | null)[] | null;
  probeSets: (getConfig_nimbusConfig_probeSets | null)[] | null;
  targetingConfigSlug: (getConfig_nimbusConfig_targetingConfigSlug | null)[] | null;
}

export interface getConfig {
  nimbusConfig: getConfig_nimbusConfig | null;
}
