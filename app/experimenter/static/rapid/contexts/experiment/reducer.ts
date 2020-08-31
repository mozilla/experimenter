import produce, { Draft } from "immer";

import {
  ExperimentData,
  ExperimentErrors,
  ExperimentReducerAction,
  ExperimentErrorReducerAction,
  ExperimentReducerActionType,
  ExperimentErrorReducerActionType,
} from "experimenter-types/experiment";

const reducer = produce(
  (draft: Draft<ExperimentData>, action: ExperimentReducerAction) => {
    switch (action.type) {
      case ExperimentReducerActionType.UPDATE_STATE: {
        return action.state;
      }

      /* istanbul ignore next */
      default: {
        return draft;
      }
    }
  },
);

export const errorReducer = produce(
  (draft: Draft<ExperimentErrors>, action: ExperimentErrorReducerAction) => {
    switch (action.type) {
      case ExperimentErrorReducerActionType.UPDATE_ERRORS: {
        return action.errors;
      }

      /* istanbul ignore next */
      default: {
        return draft;
      }
    }
  },
);
export default reducer;
