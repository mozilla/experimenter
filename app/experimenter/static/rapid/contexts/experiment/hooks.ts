import React from "react";

import context from "experimenter-rapid/contexts/experiment/context";
import {
  ExperimentData,
  ExperimentReducerAction,
} from "experimenter-types/experiment";

export function useExperimentState(): ExperimentData {
  const { state } = React.useContext(context);
  return state;
}

export function useExperimentDispatch(): React.Dispatch<
  ExperimentReducerAction
> {
  const { dispatch } = React.useContext(context);
  return dispatch;
}
