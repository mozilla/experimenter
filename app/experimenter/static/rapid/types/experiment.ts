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
  status: ExperimentStatus;
}

export enum ExperimentReducerActionType {
  UPDATE_STATE = "UPDATE_STATE",
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
