/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type AnalysisBasis = "enrollments" | "exposures";
export type LogSource = "jetstream" | "sizing" | "jetstream-preview";
export type AnalysisErrors = AnalysisError[];
export type Feature = FeatureWithExposure | FeatureWithoutExposure;
export type FeatureVariableType = "int" | "string" | "boolean" | "json";
export type PrefBranch = "default" | "user";
export type SizingReleaseChannel = "release" | "beta" | "nightly";
export type SizingUserType = "new" | "existing";
export type Statistics = Statistic[];

export interface AnalysisError {
  analysis_basis?: AnalysisBasis;
  source?: LogSource;
  exception?: string;
  exception_type?: string;
  experiment?: string;
  filename: string;
  func_name: string;
  log_level: string;
  message: string;
  metric?: string;
  segment?: string;
  statistic?: string;
  timestamp: string;
}
export interface ExternalConfig {
  reference_branch?: string;
  end_date?: string;
  start_date?: string;
  enrollment_period?: number;
  skip?: boolean;
  url: string;
}
export interface FeatureManifest {
  [k: string]: Feature;
}
/**
 * A feature that has exposure.
 */
export interface FeatureWithExposure {
  description?: string;
  isEarlyStartup?: boolean;
  variables: {
    [k: string]: FeatureVariable;
  };
  schema?: NimbusFeatureSchema;
  hasExposure: true;
  exposureDescription: string;
}
export interface FeatureVariable {
  description?: string;
  enum?: string[];
  fallbackPref?: string;
  type?: FeatureVariableType;
  setPref?: string | SetPref;
}
export interface SetPref {
  branch: PrefBranch;
  pref: string;
}
export interface NimbusFeatureSchema {
  uri: string;
  path: string;
}
/**
 * A feature without exposure.
 */
export interface FeatureWithoutExposure {
  description?: string;
  isEarlyStartup?: boolean;
  variables: {
    [k: string]: FeatureVariable;
  };
  schema?: NimbusFeatureSchema;
  hasExposure: false;
}
export interface Metadata {
  analysis_start_time?: string;
  external_config?: ExternalConfig;
  metrics: {
    [k: string]: Metric;
  };
  outcomes?: {
    [k: string]: Outcome;
  };
  schema_version?: number;
}
export interface Metric {
  analysis_bases: AnalysisBasis[];
  bigger_is_better: boolean;
  description?: string;
  friendly_name?: string;
}
export interface Outcome {
  commit_hash?: string;
  default_metrics: string[];
  description: string;
  friendly_name: string;
  metrics: string[];
  slug: string;
}
export interface NimbusExperiment {
  schemaVersion: string;
  slug: string;
  id: string;
  appName: string;
  appId: string;
  channel: string;
  userFacingName: string;
  userFacingDescription: string;
  isEnrollmentPaused: boolean;
  isRollout?: boolean;
  bucketConfig: ExperimentBucketConfig;
  outcomes?: ExperimentOutcome[];
  featureIds: string[];
  branches: (
    | ExperimentSingleFeatureBranch
    | ExperimentMultiFeatureDesktopBranch
    | ExperimentMultiFeatureMobileBranch
  )[];
  targeting?: string;
  startDate?: string;
  enrollmentEndDate?: string;
  endDate?: string;
  proposedDuration?: number;
  proposedEnrollment?: number;
  referenceBranch?: string;
  featureValidationOptOut?: boolean;
  localizations?: {
    [k: string]: unknown;
  };
  locales?: string[];
}
export interface ExperimentBucketConfig {
  randomizationUnit: string;
  namespace: string;
  start: number;
  count: number;
  total: number;
}
export interface ExperimentOutcome {
  slug: string;
  priority: string;
}
export interface ExperimentSingleFeatureBranch {
  slug: string;
  ratio: number;
  feature: ExperimentFeatureConfig;
}
export interface ExperimentFeatureConfig {
  featureId: string;
  enabled?: boolean;
  value: {
    [k: string]: unknown;
  };
}
export interface ExperimentMultiFeatureDesktopBranch {
  slug: string;
  ratio: number;
  feature: ExperimentFeatureConfig;
  features: ExperimentFeatureConfig[];
}
export interface ExperimentMultiFeatureMobileBranch {
  slug: string;
  ratio: number;
  features: ExperimentFeatureConfig[];
}
/**
 * `extra=Extra.allow` is needed for the pydantic2ts generation of
 * typescript definitions. Without this, models with only a custom
 * __root__ dictionary field will generate as empty types.
 *
 * See https://github.com/phillipdupuis/pydantic-to-typescript/blob/master/pydantic2ts/cli/script.py#L150-L153
 * and https://github.com/phillipdupuis/pydantic-to-typescript/issues/39
 * for more info.
 *
 * If this is fixed we should remove `extra=Extra.allow`.
 */
export interface SampleSizes {
  [k: string]: SizingByUserType;
}
/**
 * `extra=Extra.allow` is needed for the pydantic2ts generation of
 * typescript definitions. Without this, models with only a custom
 * __root__ dictionary field will generate as empty types.
 *
 * See https://github.com/phillipdupuis/pydantic-to-typescript/blob/master/pydantic2ts/cli/script.py#L150-L153
 * and https://github.com/phillipdupuis/pydantic-to-typescript/issues/39
 * for more info.
 *
 * If this is fixed we should remove `extra=Extra.allow`.
 */
export interface SizingByUserType {
  [k: string]: SizingTarget;
}
export interface SizingTarget {
  target_recipe: SizingRecipe;
  sample_sizes: {
    [k: string]: SizingDetails;
  };
}
export interface SizingRecipe {
  app_id: string;
  channel: SizingReleaseChannel;
  locale?: string;
  language?: string;
  country: string;
  new_or_existing: SizingUserType;
}
export interface SizingDetails {
  metrics: {
    [k: string]: SizingMetric;
  };
  parameters: SizingParameters;
}
export interface SizingMetric {
  number_of_clients_targeted: number;
  sample_size_per_branch: number;
  population_percent_per_branch: number;
}
export interface SizingParameters {
  power: number;
  effect_size: number;
}
export interface Statistic {
  metric: string;
  statistic: string;
  branch: string;
  parameter?: number;
  comparison?: string;
  comparison_to_branch?: string;
  ci_width?: number;
  point?: number;
  lower?: number;
  upper?: number;
  p_value?: number;
  segment?: string;
  analysis_basis?: AnalysisBasis;
  window_index?: string;
}
