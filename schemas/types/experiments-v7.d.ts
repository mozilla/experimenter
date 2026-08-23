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

/**
 * A Nimbus experiment for V7.
 */
export interface NimbusExperimentV7 {
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
   * The channels available for the experiment.
   * This field should be preferred over the channel field.
   */
  channels?: string[];
  /**
   * Branch configuration for the experiment.
   */
  branches: ExperimentBranchV7[];
  /**
   * All documentation links associated with this experiment.
   */
  documentationLinks: DocumentationLink[];
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
export interface ExperimentBranchV7 {
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
   * A description of the branch.
   */
  description: string;
  /**
   * The URLs of any screenshots associated with the branch.
   */
  screenshots: string[];
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
export interface DocumentationLink {
  /**
   * The name associated with the link.
   */
  title: string;
  /**
   * The URL associated with the link.
   */
  link: string;
}
