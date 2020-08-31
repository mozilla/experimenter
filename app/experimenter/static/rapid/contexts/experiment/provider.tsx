import React from "react";
import { useParams } from "react-router";

import { fetchExperiment } from "experimenter-rapid/contexts/experiment/actions";
import context, {
  INITIAL_CONTEXT,
} from "experimenter-rapid/contexts/experiment/context";
import reducer, {
  errorReducer,
} from "experimenter-rapid/contexts/experiment/reducer";
import {
  Action,
  ErrorAction,
  ExperimentData,
  ExperimentErrors,
} from "experimenter-types/experiment";

const ExperimentProvider: React.FC<{
  initialState?: ExperimentData;
  errorState?: ExperimentErrors;
}> = ({
  children,
  initialState = INITIAL_CONTEXT.state,
  errorState = INITIAL_CONTEXT.errors,
}) => {
  const [state, reducerDispatch] = React.useReducer(reducer, initialState);
  const [errors, errorReducerDispatch] = React.useReducer(
    errorReducer,
    errorState,
  );
  const { experimentSlug } = useParams();
  const { Provider } = context;

  const dispatch = (action: Action) => action(state, reducerDispatch);
  const errorDispatch = (action: ErrorAction) =>
    action(errors, errorReducerDispatch);
  React.useEffect(() => {
    if (!experimentSlug) {
      return;
    }

    dispatch(fetchExperiment(experimentSlug));
  }, [experimentSlug]);

  return (
    <Provider value={{ state, errors, dispatch, errorDispatch }}>
      {children}
    </Provider>
  );
};

export default ExperimentProvider;
