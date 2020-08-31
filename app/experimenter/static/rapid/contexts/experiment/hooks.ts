import React from "react";

import context from "experimenter-rapid/contexts/experiment/context";
import {
  Dispatch,
  ErrorDispatch,
  ExperimentData,
  ExperimentErrors,
} from "experimenter-types/experiment";

export function useExperimentState(): ExperimentData {
  const { state } = React.useContext(context);
  return state;
}

export function useExperimentDispatch(): Dispatch {
  const { dispatch } = React.useContext(context);
  return dispatch;
}

export function useExperimentErrorState(): ExperimentErrors {
  const { errors } = React.useContext(context);
  return errors;
}

export function useExperimentErrorDispatch(): ErrorDispatch {
  const { errorDispatch } = React.useContext(context);
  return errorDispatch;
}
