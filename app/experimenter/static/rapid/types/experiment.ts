export interface ExperimentData {
  name: string;
  objectives: string;
  features: Array<string>;
  audience: string;
  owner?: string;
  slug?: string;
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
