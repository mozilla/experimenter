import produce, { Draft } from "immer";

import {
  ExperimentData,
  ExperimentReducerAction,
  ExperimentReducerActionType,
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

export default reducer;
