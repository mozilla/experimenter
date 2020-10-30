export enum ExperimentStatus {
  DRAFT = "Draft",
  REVIEW = "Review",
  ACCEPTED = "Accepted",
  LIVE = "Live",
  COMPLETE = "Complete",
  REJECTED = "Rejected",
}

export enum FirefoxChannel {
  NIGHTLY = "Nightly",
  BETA = "Beta",
  RELEASE = "Release",
}

export interface Variant {
  slug?: string;
  name: string;
  description: string;
  ratio: number;
  is_control: boolean;
  value: string;
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

export interface ExperimentAnalysis {
  daily: Array<AnalysisPoint>;
  weekly: Array<AnalysisPoint>;
  overall: { [branch: string]: BranchDescription };
  show_analysis: boolean;
}

export interface ExperimentData {
  audience: string;
  bugzilla_url?: string;
  features: Array<string>;
  firefox_min_version: string;
  firefox_channel: FirefoxChannel;
  monitoring_dashboard_url?: string;
  name: string;
  objectives: string;
  owner?: string;
  slug?: string;
  recipe_slug?: string;
  reject_feedback?: RejectFeedback;
  status: ExperimentStatus;
  analysis?: ExperimentAnalysis;
  variants: Array<Variant>;
}

export enum ExperimentReducerActionType {
  UPDATE_STATE = "UPDATE_STATE",
}

interface RejectFeedback {
  message: string;
  changed_on: string;
}
export interface ExperimentReducerAction {
  type: ExperimentReducerActionType.UPDATE_STATE;
  state: ExperimentData;
}

export type Action = (
  experimentData: ExperimentData,
  dispatch: React.Dispatch<ExperimentReducerAction>,
) => void;

export type Dispatch = (action: Action) => void;
