/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models.
/* Do not modify by hand - update the pydantic models and re-run
 * make schemas_build
 */

export type HighwindAnalysisUnit = "client_id" | "profile_group_id";
export type HighwindWindowKind = "cumulative" | "disjoint";
export type HighwindCellState = "not_started" | "insufficient_data" | "forming" | "confident" | "error";
export type HighwindDirection = "positive" | "negative" | "neutral";
export type HighwindLogLevel = "WARNING" | "ERROR";

export interface HighwindAnalysis {
  metadata: HighwindMetadata;
  segments: HighwindSegment[];
  metrics: HighwindMetricResult[];
  errors: HighwindError[];
}
export interface HighwindMetadata {
  schema_version: number;
  experiment_slug: string;
  as_of_date: string;
  generated_at: string;
  pipeline_version: string;
  start_date: string;
  end_date: string | null;
  analysis_unit: HighwindAnalysisUnit;
  reference_branch: string;
  branches: string[];
}
export interface HighwindSegment {
  slug: string;
  friendly_name: string;
  description?: string | null;
  branches: HighwindSegmentBranch[];
}
export interface HighwindSegmentBranch {
  branch: string;
  units: number;
}
export interface HighwindMetricResult {
  slug: string;
  friendly_name: string;
  description?: string | null;
  segments: HighwindSegmentResult[];
}
export interface HighwindSegmentResult {
  segment: string;
  windows: HighwindWindowResult[];
}
export interface HighwindWindowResult {
  window: HighwindWindow;
  is_summary: boolean;
  branches: HighwindBranchValue[];
  comparisons: HighwindComparison[];
}
export interface HighwindWindow {
  kind: HighwindWindowKind;
  start_day: number;
  end_day: number;
  matures_on: string | null;
}
export interface HighwindBranchValue {
  branch: string;
  n: number;
  value: number | null;
  lower: number | null;
  upper: number | null;
}
export interface HighwindComparison {
  branch: string;
  reference_branch: string;
  state: HighwindCellState;
  direction: HighwindDirection;
  relative_shift: number | null;
  lower: number | null;
  upper: number | null;
  n_reference: number | null;
  n_treatment: number | null;
  error: string | null;
}
export interface HighwindError {
  timestamp: string;
  log_level: HighwindLogLevel;
  message: string;
  exception_type: string | null;
  exception: string | null;
  filename: string;
  func_name: string;
  metric: string | null;
  segment: string | null;
  window: HighwindWindow | null;
}
