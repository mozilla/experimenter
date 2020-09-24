import React from "react";
import { useParams } from "react-router";

import { fetchExperiment } from "experimenter-rapid/contexts/experiment/actions";
import context, {
  INITIAL_CONTEXT,
} from "experimenter-rapid/contexts/experiment/context";
import reducer from "experimenter-rapid/contexts/experiment/reducer";
import { Action, ExperimentData } from "experimenter-types/experiment";

const ExperimentProvider: React.FC<{ initialState?: ExperimentData }> = ({
  children,
  initialState = INITIAL_CONTEXT.state,
}) => {
  const [state, reducerDispatch] = React.useReducer(reducer, initialState);
  const { experimentSlug } = useParams();
  const { Provider } = context;

  const dispatch = (action: Action) => action(state, reducerDispatch);
  React.useEffect(() => {
    if (!experimentSlug) {
      return;
    }

    dispatch(fetchExperiment(experimentSlug));
  }, [experimentSlug]);

  return <Provider value={{ state, dispatch }}>{children}</Provider>;
};

export default ExperimentProvider;
