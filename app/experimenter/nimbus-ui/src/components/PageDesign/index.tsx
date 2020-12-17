/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";

const PageDesign: React.FunctionComponent<RouteComponentProps> = () => {
  return (
    <AppLayoutWithExperiment
      title="Design"
      testId="PageDesign"
      analysisRequired
      redirect={({ status }) => {
        if (!status?.locked) {
          return "edit/overview";
        }
      }}
    >
      {({ experiment }) => <p>{experiment.name}</p>}
    </AppLayoutWithExperiment>
  );
};

export default PageDesign;
