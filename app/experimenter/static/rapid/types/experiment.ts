export interface ExperimentData {
  name: string;
  objectives: string;
  features: Array<string>;
  audience: string;
  firefox_min_version: string;
  owner?: string;
  slug?: string;
  bugzilla_url?: string;
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
