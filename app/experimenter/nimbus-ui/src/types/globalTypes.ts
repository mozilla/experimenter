/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum NimbusExperimentApplication {
  DESKTOP = "DESKTOP",
  FENIX = "FENIX",
}

export enum NimbusExperimentChannel {
  DESKTOP_BETA = "DESKTOP_BETA",
  DESKTOP_NIGHTLY = "DESKTOP_NIGHTLY",
  DESKTOP_RELEASE = "DESKTOP_RELEASE",
  FENIX_BETA = "FENIX_BETA",
  FENIX_NIGHTLY = "FENIX_NIGHTLY",
  FENIX_RELEASE = "FENIX_RELEASE",
  REFERENCE_RELEASE = "REFERENCE_RELEASE",
}

export enum NimbusExperimentFirefoxMinVersion {
  FIREFOX_100 = "FIREFOX_100",
  FIREFOX_80 = "FIREFOX_80",
  FIREFOX_81 = "FIREFOX_81",
  FIREFOX_82 = "FIREFOX_82",
  FIREFOX_83 = "FIREFOX_83",
  FIREFOX_84 = "FIREFOX_84",
  FIREFOX_85 = "FIREFOX_85",
  FIREFOX_86 = "FIREFOX_86",
  FIREFOX_87 = "FIREFOX_87",
  FIREFOX_88 = "FIREFOX_88",
  FIREFOX_89 = "FIREFOX_89",
  FIREFOX_90 = "FIREFOX_90",
  FIREFOX_91 = "FIREFOX_91",
  FIREFOX_92 = "FIREFOX_92",
  FIREFOX_93 = "FIREFOX_93",
  FIREFOX_94 = "FIREFOX_94",
  FIREFOX_95 = "FIREFOX_95",
  FIREFOX_96 = "FIREFOX_96",
  FIREFOX_97 = "FIREFOX_97",
  FIREFOX_98 = "FIREFOX_98",
  FIREFOX_99 = "FIREFOX_99",
}

export enum NimbusExperimentStatus {
  ACCEPTED = "ACCEPTED",
  COMPLETE = "COMPLETE",
  DRAFT = "DRAFT",
  LIVE = "LIVE",
  REVIEW = "REVIEW",
}

export enum NimbusExperimentTargetingConfigSlug {
  ALL_ENGLISH = "ALL_ENGLISH",
  FIRST_RUN = "FIRST_RUN",
  US_ONLY = "US_ONLY",
}

/**
 * An enumeration.
 */
export enum NimbusFeatureConfigApplication {
  FENIX = "FENIX",
  FIREFOX_DESKTOP = "FIREFOX_DESKTOP",
}

/**
 * An enumeration.
 */
export enum NimbusProbeKind {
  EVENT = "EVENT",
  SCALAR = "SCALAR",
}

export interface CreateExperimentInput {
  clientMutationId?: string | null;
  name: string;
  application: NimbusExperimentApplication;
  publicDescription?: string | null;
  hypothesis: string;
}

export interface UpdateExperimentInput {
  clientMutationId?: string | null;
  name?: string | null;
  application?: NimbusExperimentApplication | null;
  publicDescription?: string | null;
  hypothesis?: string | null;
  id: string;
}

//==============================================================
// END Enums and Input Objects
//==============================================================
