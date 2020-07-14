import React from "react";

import { Action, ExperimentData } from "experimenter-types/experiment";

export const INITIAL_CONTEXT: {
  state: ExperimentData;
  dispatch: (action: Action) => void;
} = {
  state: {
    name: "",
    objectives: "",
    features: [],
    audience: "",
  },
  dispatch: (action: Action) => {
    /* istanbul ignore next */
    console.log(action);
  },
};

const context = React.createContext(INITIAL_CONTEXT);
export default context;
