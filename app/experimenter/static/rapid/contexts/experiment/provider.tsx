import React from "react";
import { useParams } from "react-router";

import context, {
  INITIAL_CONTEXT,
} from "experimenter-rapid/contexts/experiment/context";
import reducer from "experimenter-rapid/contexts/experiment/reducer";
import {
  ExperimentData,
  ExperimentReducerActionType,
} from "experimenter-types/experiment";

const ExperimentProvider: React.FC<{ initialState?: ExperimentData }> = ({
  children,
  initialState = INITIAL_CONTEXT.state,
}) => {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const { experimentSlug } = useParams();
  const { Provider } = context;

  React.useEffect(() => {
    if (!experimentSlug) {
      return;
    }

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

    fetchData();
  }, [experimentSlug]);

  return <Provider value={{ state, dispatch }}>{children}</Provider>;
};

export default ExperimentProvider;
