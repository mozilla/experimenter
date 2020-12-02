/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import { useConfig } from "../../hooks";
import FormAudience from "../FormAudience";

const PageEditAudience: React.FunctionComponent<RouteComponentProps> = () => {
  const config = useConfig();

  return (
    <AppLayoutWithExperiment title="Audience" testId="PageEditAudience">
      {({ experiment }) => (
        <FormAudience
          {...{
            experiment,
            config,
          }}
        />
      )}
    </AppLayoutWithExperiment>
  );
};

export default PageEditAudience;
