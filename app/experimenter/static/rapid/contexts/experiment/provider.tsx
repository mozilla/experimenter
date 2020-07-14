import React from "react";
import { useParams } from "react-router";

import context, {
  INITIAL_CONTEXT,
} from "experimenter-rapid/contexts/experiment/context";
import reducer from "experimenter-rapid/contexts/experiment/reducer";
import {
  Action,
  ExperimentData,
  ExperimentReducerActionType,
} from "experimenter-types/experiment";
import { fetchExperiment } from "experimenter-rapid/contexts/experiment/actions";

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
    /*
    const fetchData = async () => {
      const response = await fetch(`/api/v3/experiments/${experimentSlug}/`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();
      dispatch({
        type: ExperimentReducerActionType.UPDATE_STATE,
        state: data,
      });
    };

 */

    dispatch(fetchExperiment(experimentSlug));
  }, [experimentSlug]);

  return <Provider value={{ state, dispatch }}>{children}</Provider>;
};

export default ExperimentProvider;
