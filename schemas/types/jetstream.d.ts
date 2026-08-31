/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models.
/* Do not modify by hand - update the pydantic models and re-run
 * make schemas_build
 */

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
