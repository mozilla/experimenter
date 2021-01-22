/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React from "react";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import Summary from "../Summary";

const PageDesign: React.FunctionComponent<RouteComponentProps> = () => {
  return (
    <AppLayoutWithExperiment
      title="Design"
      testId="PageDesign"
      analysisRequiredInSidebar
      redirect={({ status }) => {
        if (!status?.locked) {
          return "edit/overview";
        }
      }}
    >
      {({ experiment }) => <Summary {...{ experiment }} />}
    </AppLayoutWithExperiment>
  );
};

export default PageDesign;
