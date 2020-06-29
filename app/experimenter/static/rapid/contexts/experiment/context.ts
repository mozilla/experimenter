import React from "react";

import { ExperimentContext } from "experimenter-types/experiment";

export const INITIAL_CONTEXT: ExperimentContext = {
  state: {
    name: "",
    objectives: "",
  },
  dispatch(action) {
    /* istanbul ignore next */
    console.log(action);
  },
};

const context = React.createContext(INITIAL_CONTEXT);
export default context;
