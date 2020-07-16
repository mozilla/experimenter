import React from "react";

import {
  Action,
  ExperimentStatus,
  ExperimentData,
} from "experimenter-types/experiment";

export const INITIAL_CONTEXT: {
  state: ExperimentData;
  dispatch: (action: Action) => void;
} = {
  state: {
    status: ExperimentStatus.DRAFT,
    name: "",
    objectives: "",
    features: [],
    audience: "",
    firefox_min_version: "",
  },
  dispatch: (action: Action) => {
    /* istanbul ignore next */
    console.log(action);
  },
};

const context = React.createContext(INITIAL_CONTEXT);
export default context;
