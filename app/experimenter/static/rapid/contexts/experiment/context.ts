import React from "react";

import {
  Action,
  ExperimentStatus,
  ExperimentData,
  FirefoxChannel,
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
    firefox_channel: FirefoxChannel.RELEASE,
    firefox_min_version: "",
    variants: [
      {
        name: "control",
        is_control: true,
        description: "An empty branch",
        value: "",
        ratio: 50,
      },
      {
        name: "variant",
        is_control: true,
        description: "An empty branch",
        value: "",
        ratio: 50,
      },
    ],
  },
  dispatch: (action: Action) => {
    /* istanbul ignore next */
    console.log(action);
  },
};

const context = React.createContext(INITIAL_CONTEXT);
export default context;
