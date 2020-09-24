import React from "react";

import context from "experimenter-rapid/contexts/experiment/context";
import { Dispatch, ExperimentData } from "experimenter-types/experiment";

export function useExperimentState(): ExperimentData {
  const { state } = React.useContext(context);
  return state;
}

export function useExperimentDispatch(): Dispatch {
  const { dispatch } = React.useContext(context);
  return dispatch;
}
