/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models.
/* Do not modify by hand - update the pydantic models and re-run
 * make schemas_build
 */

/**
 * A unique, stable identifier for the user used as an input to bucket hashing.
 */
export type RandomizationUnit = "normandy_id" | "nimbus_id" | "user_id" | "group_id";
export type DesktopApplication = "firefox-desktop" | "firefox-desktop-background-task";
export type FeatureVariableType = "int" | "string" | "boolean" | "json";
export type PrefBranch = "default" | "user";
export type AnalysisBasis = "enrollments" | "exposures";
export type LogSource = "jetstream" | "sizing" | "jetstream-preview";
export type AnalysisErrors = AnalysisError[];
export type AnalysisSegment = "all";
export type AnalysisSignificance = "positive" | "negative" | "neutral";
export type AnalysisWindow = "daily" | "weekly" | "overall";
export type BranchComparison = "absolute" | "difference" | "relative_uplift";
export type MetricGroup = "search_metrics" | "usage_metrics" | "other_metrics";
export type MetricIngestEnum = "retained" | "search_count" | "days_of_use" | "identity";
export type SizingReleaseChannel = "release" | "beta" | "nightly";
export type SizingUserType = "new" | "existing" | "all";
export type SizingMetricName = "active_hours" | "search_count" | "days_of_use" | "tagged_search_count";
/**
 * This is the list of statistics supported in Experimenter,
 * not a complete list of statistics available in Jetstream.
 */
export type StatisticIngestEnum = "percentage" | "binomial" | "mean" | "count";
export type Statistics = Statistic[];

/**
 * A Nimbus experiment for Firefox Desktop.
 *
 * This schema is more strict than DesktopNimbusExperiment and is backwards
 * comaptible with Firefox Desktop versions less than 95. It is intended for use inside
 * Experimenter itself.
 */
export interface DesktopAllVersionsNimbusExperiment {
  /**
   * Version of the NimbusExperiment schema this experiment refers to
   */
  schemaVersion: string;
  /**
   * Unique identifier for the experiment
   */
  slug: string;
  /**
   * Unique identifier for the experiiment.
   *
   * This is a duplicate of slug, but is required field for all Remote Settings records.
   */
  id: string;
  /**
   * A slug identifying the targeted product of this experiment.
   *
   * It should be a lowercased_with_underscores name that is short and unambiguous and it should match the app_name found in https://probeinfo.telemetry.mozilla.org/glean/repositories. Examples are "fenix" and "firefox_desktop".
   */
  appName: string;
  /**
   * The platform identifier for the targeted app.
   *
   * This should match app's identifier exactly as it appears in the relevant app store listing (for relevant platforms) or the app's Glean initialization (for other platforms).
   *
   * Examples are "org.mozilla.firefox_beta" and "firefox-desktop".
   */
  appId: string;
  /**
   * A specific channel of an application such as "nightly", "beta", or "release".
   */
  channel: string;
  /**
   * Public name of the experiment that will be displayed on "about:studies".
   */
  userFacingName: string;
  /**
   * Short public description of the experiment that will be displayed on "about:studies".
   */
  userFacingDescription: string;
  /**
   * When this property is set to true, the SDK should not enroll new users into the experiment that have not already been enrolled.
   */
  isEnrollmentPaused: boolean;
  /**
   * When this property is set to true, treat this experiment as a rollout.
   *
   * Rollouts are currently handled as single-branch experiments separated from the bucketing namespace for normal experiments.
   *
   * See-also: https://mozilla-hub.atlassian.net/browse/SDK-405
   */
  isRollout?: boolean;
  bucketConfig: ExperimentBucketConfig;
  /**
   * A list of outcomes relevant to the experiment analysis.
   */
  outcomes?: ExperimentOutcome[];
  /**
   * A list of featureIds the experiment contains configurations for.
   */
  featureIds?: string[];
  /**
   * A JEXL targeting expression used to filter out experiments.
   */
  targeting?: string | null;
  /**
   * Actual publish date of the experiment.
   *
   * Note that this value is expected to be null in Remote Settings.
   */
  startDate: string | null;
  /**
   * Actual enrollment end date of the experiment.
   *
   * Note that this value is expected to be null in Remote Settings.
   */
  enrollmentEndDate?: string | null;
  /**
   * Actual end date of this experiment.
   *
   * Note that this field is expected to be null in Remote Settings.
   */
  endDate: string | null;
  /**
   * Duration of the experiment from the start date in days.
   *
   * Note that this property is only used during the analysis phase (i.e., not by the SDK).
   */
  proposedDuration?: number;
  /**
   * This represents the number of days that we expect to enroll new users.
   *
   * Note that this property is only used during the analysis phase (i.e., not by the SDK).
   */
  proposedEnrollment: number;
  /**
   * The slug of the reference branch (i.e., the branch we consider "control").
   */
  referenceBranch: string | null;
  /**
   * The list of locale codes (e.g., "en-US" or "fr") that this experiment is targeting.
   *
   * If null, all locales are targeted.
   */
  locales?: string[] | null;
  localizations?: ExperimentLocalizations | null;
  /**
   * The date that this experiment was first published to Remote Settings.
   *
   * If null, it has not yet been published.
   */
  publishedDate?: string | null;
  /**
   * Branch configuration for the experiment.
   */
  branches: DesktopAllVersionsExperimentBranch[];
  /**
   * When this property is set to true, treat this experiment as aFirefox Labs experiment
   */
  isFirefoxLabsOptIn?: boolean;
  /**
   * The group this should appear under in Firefox Labs
   */
  firefoxLabsGroup?: string | null;
  /**
   * The title shown in Firefox Labs (Fluent ID)
   */
  firefoxLabsTitle?: string | null;
  /**
   * The description shown in Firefox Labs (Fluent ID)
   */
  firefoxLabsDescription?: string | null;
  /**
   * Links that will be used with the firefoxLabsDescription Fluent ID. May be null for Firefox Labs Opt-In recipes that do not use links.
   */
  firefoxLabsDescriptionLinks?: {
    [k: string]: string;
  } | null;
  /**
   * Opt out of feature schema validation.
   */
  featureValidationOptOut?: boolean;
  /**
   * Does the experiment require a restart to take effect?
   *
   * Only used by Firefox Labs Opt-Ins.
   */
  requiresRestart?: boolean;
}
export interface ExperimentBucketConfig {
  randomizationUnit: RandomizationUnit;
  /**
   * Additional inputs to the hashing function.
   */
  namespace: string;
  /**
   * Index of the starting bucket of the range.
   */
  start: number;
  /**
   * Number of buckets in the range.
   */
  count: number;
  /**
   * The total number of buckets.
   *
   * You can assume this will always be 10000.
   */
  total: number;
}
export interface ExperimentOutcome {
  /**
   * Identifier for the outcome.
   */
  slug: string;
  /**
   * e.g., "primary" or "secondary".
   */
  priority: string;
}
/**
 * Per-locale localization substitutions.
 *
 * The top level key is the locale (e.g., "en-US" or "fr"). Each entry is a mapping of
 * string IDs to their localized equivalents.
 */
export interface ExperimentLocalizations {
  [k: string]: {
    [k: string]: string;
  };
}
/**
 * The branch definition supported on all Firefox Desktop versions.
 *
 * This version requires the feature field to be present to support older Firefox Desktop
 * clients.
 */
export interface DesktopAllVersionsExperimentBranch {
  /**
   * Identifier for the branch.
   */
  slug: string;
  /**
   * Relative ratio of population for the branch.
   *
   * e.g., if branch A=1 and branch B=3, then branch A would get 25% of the population.
   */
  ratio: number;
  /**
   * An array of feature configurations.
   */
  features: ExperimentFeatureConfig[];
  /**
   * The branch title shown in Firefox Labs (Fluent ID)
   */
  firefoxLabsTitle?: string | null;
  feature: DesktopPre95FeatureConfig;
}
export interface ExperimentFeatureConfig {
  /**
   * The identifier for the feature flag.
   */
  featureId: string;
  /**
   * The values that define the feature configuration.
   *
   * This should be validated against a schema.
   */
  value: {
    [k: string]: unknown;
  };
}
export interface DesktopPre95FeatureConfig {
  featureId: "this-is-included-for-desktop-pre-95-support";
  value: {
    [k: string]: unknown;
  };
  enabled: false;
}
/**
 * A Nimbus experiment for Firefox Desktop.
 *
 * This schema is less strict than DesktopAllVersionsNimbusExperiment and is intended for
 * use in Firefox Desktop.
 */
export interface DesktopNimbusExperiment {
  /**
   * Version of the NimbusExperiment schema this experiment refers to
   */
  schemaVersion: string;
  /**
   * Unique identifier for the experiment
   */
  slug: string;
  /**
   * Unique identifier for the experiiment.
   *
   * This is a duplicate of slug, but is required field for all Remote Settings records.
   */
  id: string;
  /**
   * A slug identifying the targeted product of this experiment.
   *
   * It should be a lowercased_with_underscores name that is short and unambiguous and it should match the app_name found in https://probeinfo.telemetry.mozilla.org/glean/repositories. Examples are "fenix" and "firefox_desktop".
   */
  appName: string;
  /**
   * The platform identifier for the targeted app.
   *
   * This should match app's identifier exactly as it appears in the relevant app store listing (for relevant platforms) or the app's Glean initialization (for other platforms).
   *
   * Examples are "org.mozilla.firefox_beta" and "firefox-desktop".
   */
  appId: string;
  /**
   * A specific channel of an application such as "nightly", "beta", or "release".
   */
  channel: string;
  /**
   * Public name of the experiment that will be displayed on "about:studies".
   */
  userFacingName: string;
  /**
   * Short public description of the experiment that will be displayed on "about:studies".
   */
  userFacingDescription: string;
  /**
   * When this property is set to true, the SDK should not enroll new users into the experiment that have not already been enrolled.
   */
  isEnrollmentPaused: boolean;
  /**
   * When this property is set to true, treat this experiment as a rollout.
   *
   * Rollouts are currently handled as single-branch experiments separated from the bucketing namespace for normal experiments.
   *
   * See-also: https://mozilla-hub.atlassian.net/browse/SDK-405
   */
  isRollout?: boolean;
  bucketConfig: ExperimentBucketConfig;
  /**
   * A list of outcomes relevant to the experiment analysis.
   */
  outcomes?: ExperimentOutcome[];
  /**
   * A list of featureIds the experiment contains configurations for.
   */
  featureIds?: string[];
  /**
   * A JEXL targeting expression used to filter out experiments.
   */
  targeting?: string | null;
  /**
   * Actual publish date of the experiment.
   *
   * Note that this value is expected to be null in Remote Settings.
   */
  startDate: string | null;
  /**
   * Actual enrollment end date of the experiment.
   *
   * Note that this value is expected to be null in Remote Settings.
   */
  enrollmentEndDate?: string | null;
  /**
   * Actual end date of this experiment.
   *
   * Note that this field is expected to be null in Remote Settings.
   */
  endDate: string | null;
  /**
   * Duration of the experiment from the start date in days.
   *
   * Note that this property is only used during the analysis phase (i.e., not by the SDK).
   */
  proposedDuration?: number;
  /**
   * This represents the number of days that we expect to enroll new users.
   *
   * Note that this property is only used during the analysis phase (i.e., not by the SDK).
   */
  proposedEnrollment: number;
  /**
   * The slug of the reference branch (i.e., the branch we consider "control").
   */
  referenceBranch: string | null;
  /**
   * The list of locale codes (e.g., "en-US" or "fr") that this experiment is targeting.
   *
   * If null, all locales are targeted.
   */
  locales?: string[] | null;
  localizations?: ExperimentLocalizations | null;
  /**
   * The date that this experiment was first published to Remote Settings.
   *
   * If null, it has not yet been published.
   */
  publishedDate?: string | null;
  /**
   * Branch configuration for the experiment.
   */
  branches: DesktopExperimentBranch[];
  /**
   * When this property is set to true, treat this experiment as aFirefox Labs experiment
   */
  isFirefoxLabsOptIn?: boolean;
  /**
   * The group this should appear under in Firefox Labs
   */
  firefoxLabsGroup?: string | null;
  /**
   * The title shown in Firefox Labs (Fluent ID)
   */
  firefoxLabsTitle?: string | null;
  /**
   * The description shown in Firefox Labs (Fluent ID)
   */
  firefoxLabsDescription?: string | null;
  /**
   * Links that will be used with the firefoxLabsDescription Fluent ID. May be null for Firefox Labs Opt-In recipes that do not use links.
   */
  firefoxLabsDescriptionLinks?: {
    [k: string]: string;
  } | null;
  /**
   * Opt out of feature schema validation.
   */
  featureValidationOptOut?: boolean;
  /**
   * Does the experiment require a restart to take effect?
   *
   * Only used by Firefox Labs Opt-Ins.
   */
  requiresRestart?: boolean;
}
/**
 * The branch definition supported on Firefox Desktop 95+.
 */
export interface DesktopExperimentBranch {
  /**
   * Identifier for the branch.
   */
  slug: string;
  /**
   * Relative ratio of population for the branch.
   *
   * e.g., if branch A=1 and branch B=3, then branch A would get 25% of the population.
   */
  ratio: number;
  /**
   * An array of feature configurations.
   */
  features: ExperimentFeatureConfig[];
  /**
   * The branch title shown in Firefox Labs (Fluent ID)
   */
  firefoxLabsTitle?: string | null;
}
/**
 * A Nimbus experiment for Nimbus SDK-based applications.
 */
export interface SdkNimbusExperiment {
  /**
   * Version of the NimbusExperiment schema this experiment refers to
   */
  schemaVersion: string;
  /**
   * Unique identifier for the experiment
   */
  slug: string;
  /**
   * Unique identifier for the experiiment.
   *
   * This is a duplicate of slug, but is required field for all Remote Settings records.
   */
  id: string;
  /**
   * A slug identifying the targeted product of this experiment.
   *
   * It should be a lowercased_with_underscores name that is short and unambiguous and it should match the app_name found in https://probeinfo.telemetry.mozilla.org/glean/repositories. Examples are "fenix" and "firefox_desktop".
   */
  appName: string;
  /**
   * The platform identifier for the targeted app.
   *
   * This should match app's identifier exactly as it appears in the relevant app store listing (for relevant platforms) or the app's Glean initialization (for other platforms).
   *
   * Examples are "org.mozilla.firefox_beta" and "firefox-desktop".
   */
  appId: string;
  /**
   * A specific channel of an application such as "nightly", "beta", or "release".
   */
  channel: string;
  /**
   * Public name of the experiment that will be displayed on "about:studies".
   */
  userFacingName: string;
  /**
   * Short public description of the experiment that will be displayed on "about:studies".
   */
  userFacingDescription: string;
  /**
   * When this property is set to true, the SDK should not enroll new users into the experiment that have not already been enrolled.
   */
  isEnrollmentPaused: boolean;
  /**
   * When this property is set to true, treat this experiment as a rollout.
   *
   * Rollouts are currently handled as single-branch experiments separated from the bucketing namespace for normal experiments.
   *
   * See-also: https://mozilla-hub.atlassian.net/browse/SDK-405
   */
  isRollout?: boolean;
  bucketConfig: ExperimentBucketConfig;
  /**
   * A list of outcomes relevant to the experiment analysis.
   */
  outcomes?: ExperimentOutcome[];
  /**
   * A list of featureIds the experiment contains configurations for.
   */
  featureIds?: string[];
  /**
   * A JEXL targeting expression used to filter out experiments.
   */
  targeting?: string | null;
  /**
   * Actual publish date of the experiment.
   *
   * Note that this value is expected to be null in Remote Settings.
   */
  startDate: string | null;
  /**
   * Actual enrollment end date of the experiment.
   *
   * Note that this value is expected to be null in Remote Settings.
   */
  enrollmentEndDate?: string | null;
  /**
   * Actual end date of this experiment.
   *
   * Note that this field is expected to be null in Remote Settings.
   */
  endDate: string | null;
  /**
   * Duration of the experiment from the start date in days.
   *
   * Note that this property is only used during the analysis phase (i.e., not by the SDK).
   */
  proposedDuration?: number;
  /**
   * This represents the number of days that we expect to enroll new users.
   *
   * Note that this property is only used during the analysis phase (i.e., not by the SDK).
   */
  proposedEnrollment: number;
  /**
   * The slug of the reference branch (i.e., the branch we consider "control").
   */
  referenceBranch: string | null;
  /**
   * The list of locale codes (e.g., "en-US" or "fr") that this experiment is targeting.
   *
   * If null, all locales are targeted.
   */
  locales?: string[] | null;
  /**
   * Per-locale localization substitutions.
   */
  localizations?: ExperimentLocalizations | null;
  /**
   * The date that this experiment was first published to Remote Settings.
   *
   * If null, it has not yet been published.
   */
  publishedDate?: string | null;
  /**
   * Branch configuration for the SDK experiment.
   */
  branches: SdkExperimentBranch[];
}
/**
 * The branch definition for SDK-based applications.
 *
 * Supported on Firefox for Android 96+, Firefox for iOS 39+, and all versions of Cirrus.
 */
export interface SdkExperimentBranch {
  /**
   * Identifier for the branch.
   */
  slug: string;
  /**
   * Relative ratio of population for the branch.
   *
   * e.g., if branch A=1 and branch B=3, then branch A would get 25% of the population.
   */
  ratio: number;
  /**
   * An array of feature configurations.
   */
  features: ExperimentFeatureConfig[];
}
/**
 * A feature.
 */
export interface DesktopFeature {
  /**
   * The description of the feature.
   */
  description: string;
  /**
   * Whether or not this feature records exposure telemetry.
   */
  hasExposure: boolean;
  /**
   * A description of the exposure telemetry collected by this feature.
   *
   * Only required if hasExposure is true.
   */
  exposureDescription?: string;
  /**
   * The owner of the feature.
   */
  owner: string;
  /**
   * If true, the feature values will be cached in prefs so that they can be read before Nimbus is initialized during Firefox startup.
   */
  isEarlyStartup?: boolean;
  /**
   * The applications that can enroll in experiments for this feature.
   *
   * Defaults to "firefox-desktop".
   */
  applications?: DesktopApplication[];
  /**
   * The variables that this feature can set.
   */
  variables: {
    [k: string]: DesktopFeatureVariable;
  };
  schema?: NimbusFeatureSchema;
  /**
   * If true, clients can enroll in multiple experiments and rollouts that use this feature.
   */
  allowCoenrollment?: boolean;
}
/**
 * A feature variable.
 */
export interface DesktopFeatureVariable {
  /**
   * A description of the feature.
   */
  description: string;
  type: FeatureVariableType;
  /**
   * An optional list of possible string or integer values.
   *
   * Only allowed when type is string or int.
   *
   * The types in the enum must match the type of the field.
   */
  enum?: string[] | number[];
  /**
   * A pref that provides the default value for a feature when none is present.
   */
  fallbackPref?: string;
  /**
   * A pref that should be set to the value of this variable when enrolling in experiments.
   *
   * Using a string is deprecated and unsupported in Firefox 124+.
   */
  setPref?: string | SetPref;
}
export interface SetPref {
  branch: PrefBranch;
  /**
   * The name of the pref to set.
   */
  pref: string;
}
/**
 * Information about a JSON schema.
 */
export interface NimbusFeatureSchema {
  /**
   * The resource:// or chrome:// URI that can be loaded at runtime within Firefox.
   *
   * Required by Firefox so that Nimbus can import the schema for validation.
   */
  uri: string;
  /**
   * The path to the schema file in the source checkout.
   *
   * Required by Experimenter so that it can find schema files in source checkouts.
   */
  path: string;
}
/**
 * The Firefox Desktop-specific feature manifest.
 *
 * Firefox Desktop requires different fields for its features compared to the general
 * Nimbus feature manifest.
 */
export interface DesktopFeatureManifest {
  [k: string]: DesktopFeature;
}
/**
 * The SDK-specific feature manifest.
 */
export interface SdkFeatureManifest {
  [k: string]: SdkFeature;
}
/**
 * A feature.
 */
export interface SdkFeature {
  /**
   * The description of the feature.
   */
  description: string;
  /**
   * Whether or not this feature records exposure telemetry.
   */
  hasExposure: boolean;
  /**
   * A description of the exposure telemetry collected by this feature.
   *
   * Only required if hasExposure is true.
   */
  exposureDescription?: string;
  /**
   * The variables that this feature can set.
   */
  variables: {
    [k: string]: SdkFeatureVariable;
  };
  /**
   * If true, clients can enroll in multiple experiments and rollouts that use this feature.
   */
  "allow-coenrollment"?: boolean;
}
/**
 * A feature variable.
 */
export interface SdkFeatureVariable {
  /**
   * A description of the feature.
   */
  description: string;
  type: FeatureVariableType;
  /**
   * An optional list of possible string values.
   *
   * Only allowed when type is string.
   */
  enum?: string[];
}
export interface AnalysisError {
  analysis_basis?: AnalysisBasis | null;
  source?: LogSource | null;
  exception?: string | null;
  exception_type?: string | null;
  experiment?: string | null;
  filename: string;
  func_name: string;
  log_level: string;
  message: string;
  metric?: string | null;
  segment?: string | null;
  statistic?: string | null;
  timestamp: string;
}
export interface ConfigVersions {
  metric_definitions?: ConfigVersionDetails[] | null;
  jetstream_image?: ConfigVersionDetails | null;
}
export interface ConfigVersionDetails {
  path?: string | null;
  revision?: string | null;
}
export interface ExternalConfig {
  reference_branch?: string | null;
  end_date?: string | null;
  start_date?: string | null;
  enrollment_period?: number | null;
  skip?: boolean | null;
  url: string;
}
export interface Metadata {
  analysis_start_time?: string | null;
  external_config?: ExternalConfig | null;
  metrics: {
    [k: string]: Metric;
  };
  outcomes?: {
    [k: string]: Outcome;
  };
  version_info?: ConfigVersions | null;
  version_date?: string | null;
  schema_version?: number;
}
export interface Metric {
  analysis_bases: AnalysisBasis[];
  bigger_is_better: boolean;
  description?: string | null;
  friendly_name?: string | null;
}
export interface Outcome {
  commit_hash?: string | null;
  default_metrics: string[];
  description: string;
  friendly_name: string;
  metrics: string[];
  slug: string;
}
export interface SampleSizes {
  [k: string]: SizingByUserType;
}
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
  locale?: string | null;
  language?: string | null;
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
  parameter?: number | null;
  comparison?: string | null;
  comparison_to_branch?: string | null;
  ci_width?: number | null;
  point?: number | null;
  lower?: number | null;
  upper?: number | null;
  segment?: string;
  analysis_basis?: AnalysisBasis | null;
  window_index?: string | null;
}
