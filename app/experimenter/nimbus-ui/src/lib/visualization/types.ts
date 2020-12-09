/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

export interface AnalysisData {
  daily: AnalysisPoint[];
  weekly: AnalysisPoint[];
  overall: { [branch: string]: BranchDescription };
  show_analysis: boolean;
  other_metrics?: { [metric: string]: string };
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
  window_index?: string;
}

export interface BranchDescription {
  is_control: boolean;
  branch_data: {
    [metric: string]: {
      [index: string]: any;
      absolute: {
        point: number;
        lower?: number;
        upper?: number;
        count?: number;
      };
      difference: {
        point?: number;
        lower?: number;
        upper?: number;
      };
      relative_uplift: {
        point?: number;
        lower?: number;
        upper?: number;
      };
      percent?: number;
      significance?: string;
    };
  };
}
