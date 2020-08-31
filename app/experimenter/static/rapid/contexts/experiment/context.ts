import React from "react";

import {
  Action,
  ExperimentStatus,
  ExperimentData,
  ExperimentErrors,
  FirefoxChannel,
  ErrorAction,
} from "experimenter-types/experiment";

export const INITIAL_CONTEXT: {
  state: ExperimentData;
  errors: ExperimentErrors;
  dispatch: (action: Action) => void;
  errorDispatch: (errorAction: ErrorAction) => void;
} = {
  state: {
    status: ExperimentStatus.DRAFT,
    name: "",
    objectives: "",
    features: [],
    audience: "",
    firefox_channel: FirefoxChannel.RELEASE,
    firefox_min_version: "",
    variants: [
      {
        name: "control",
        is_control: true,
        description: "An empty branch",
        value: "",
        ratio: 1,
      },
      {
        name: "variant",
        is_control: false,
        description: "An empty branch",
        value: "",
        ratio: 1,
      },
    ],
  },
  errors: {},
  dispatch: (action: Action) => {
    /* istanbul ignore next */
    console.log(action);
  },
  errorDispatch: (errorAction: ErrorAction) => {
    /* istanbul ignore next */
    console.log(errorAction);
  },
};

const context = React.createContext(INITIAL_CONTEXT);
export default context;
