/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

export interface AnalysisData {
  daily: AnalysisPoint[] | null;
  weekly: { [branch: string]: BranchDescription } | null;
  overall: { [branch: string]: BranchDescription } | null;
  show_analysis: boolean;
  metadata?: Metadata;
  other_metrics?: { [metric: string]: string };
}

export type AnalysisDataOverall = Exclude<AnalysisData["overall"], null>;
export type AnalysisDataWeekly = Exclude<AnalysisData["weekly"], null>;

export interface Metadata {
  metrics: { [metric: string]: MetadataPoint };
  outcomes: { [outcome: string]: MetadataPoint };
}

export interface MetadataPoint {
  description: string;
  friendly_name: string;
  bigger_is_better: boolean;
}

export interface AnalysisPoint {
  metric: string;
  statistic: string;
  parameter?: string;
  branch: string;
  comparison?: string;
  ci_width?: number;
  point: number;
  lower?: number;
  upper?: number;
  window_index?: number;
}

export interface FormattedAnalysisPoint {
  point?: number;
  lower?: number;
  upper?: number;
  count?: number;
  branch?: string;
  window_index?: number;
}

export interface BranchDescription {
  is_control: boolean;
  branch_data: {
    [metric: string]: {
      [index: string]: any;
      absolute: {
        first: FormattedAnalysisPoint;
        all: FormattedAnalysisPoint[];
      };
      difference: {
        first: FormattedAnalysisPoint;
        all: FormattedAnalysisPoint[];
      };
      relative_uplift: {
        first: FormattedAnalysisPoint;
        all: FormattedAnalysisPoint[];
      };
      percent?: number;
      significance?: { [window: string]: { [window_index: string]: string } };
    };
  };
}
