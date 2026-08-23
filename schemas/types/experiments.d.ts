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
   *
   * This field is only respected by nimbus-sdk-based applications.
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
  featureIds: string[];
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
   * Opt out of feature schema validation.
   */
  featureValidationOptOut?: boolean;
  /**
   * When this property is set to true, treat this experiment as a Firefox Labs experiment
   */
  isFirefoxLabsOptIn?: boolean;
  /**
   * The title shown in Firefox Labs (Fluent ID or Resource ID)
   */
  firefoxLabsTitle?: string | null;
  /**
   * The description shown in Firefox Labs (Fluent ID or Resource ID)
   */
  firefoxLabsDescription?: string | null;
  /**
   * Links that will be used with the firefoxLabsDescription Fluent ID. May be null for Firefox Labs Opt-In recipes that do not use links.
   */
  firefoxLabsDescriptionLinks?: {
    [k: string]: string;
  } | null;
  /**
   * Does the experiment require a restart to take effect?
   *
   * Only used by Firefox Labs Opt-Ins.
   */
  requiresRestart?: boolean;
  /**
   * Branch configuration for the experiment.
   */
  branches: DesktopAllVersionsExperimentBranch[];
  /**
   * The group this should appear under in Firefox Labs
   */
  firefoxLabsGroup?: string | null;
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
   *
   * This field is only respected by nimbus-sdk-based applications.
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
  featureIds: string[];
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
   * Opt out of feature schema validation.
   */
  featureValidationOptOut?: boolean;
  /**
   * When this property is set to true, treat this experiment as a Firefox Labs experiment
   */
  isFirefoxLabsOptIn?: boolean;
  /**
   * The title shown in Firefox Labs (Fluent ID or Resource ID)
   */
  firefoxLabsTitle?: string | null;
  /**
   * The description shown in Firefox Labs (Fluent ID or Resource ID)
   */
  firefoxLabsDescription?: string | null;
  /**
   * Links that will be used with the firefoxLabsDescription Fluent ID. May be null for Firefox Labs Opt-In recipes that do not use links.
   */
  firefoxLabsDescriptionLinks?: {
    [k: string]: string;
  } | null;
  /**
   * Does the experiment require a restart to take effect?
   *
   * Only used by Firefox Labs Opt-Ins.
   */
  requiresRestart?: boolean;
  /**
   * Branch configuration for the experiment.
   */
  branches: DesktopExperimentBranch[];
  /**
   * The group this should appear under in Firefox Labs
   */
  firefoxLabsGroup?: string | null;
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
   *
   * This field is only respected by nimbus-sdk-based applications.
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
  featureIds: string[];
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
   * If true, clients should not perform feature validation.
   *
   * This field is only supported by Firefox Desktop.
   */
  featureValidationOptOut?: boolean | null;
  /**
   * When this property is set to true, treat this experiment as a Firefox Labs experiment
   */
  isFirefoxLabsOptIn?: boolean;
  /**
   * The title shown in Firefox Labs (Fluent ID or Resource ID)
   */
  firefoxLabsTitle?: string | null;
  /**
   * The description shown in Firefox Labs (Fluent ID or Resource ID)
   */
  firefoxLabsDescription?: string | null;
  /**
   * Links that will be used with the firefoxLabsDescription Fluent ID. May be null for Firefox Labs Opt-In recipes that do not use links.
   */
  firefoxLabsDescriptionLinks?: {
    [k: string]: string;
  } | null;
  /**
   * Does the experiment require a restart to take effect?
   *
   * Only used by Firefox Labs Opt-Ins.
   */
  requiresRestart?: boolean;
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
  setPref?: SetPref;
}
