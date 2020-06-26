export type ExperimentData = {
  name: string;
  objectives: string;
  owner?: string;
  slug?: string;
};

export enum ExperimentReducerActionType {
  UPDATE_STATE = "UPDATE_STATE",
}

export type ExperimentReducerAction = {
  type: ExperimentReducerActionType.UPDATE_STATE;
  state: ExperimentData;
};

export interface ExperimentContext {
  state: ExperimentData;
  dispatch: React.Dispatch<ExperimentReducerAction>;
}
