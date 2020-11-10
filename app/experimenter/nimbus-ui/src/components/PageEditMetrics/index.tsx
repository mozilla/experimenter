/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithSidebarAndData from "../AppLayoutWithSidebarAndData";

const PageEditMetrics: React.FunctionComponent<RouteComponentProps> = () => {
  return (
    <AppLayoutWithSidebarAndData title="Metrics" testId="PageEditMetrics">
      {({ experiment }) => <p>{experiment.name}</p>}
    </AppLayoutWithSidebarAndData>
  );
};

export default PageEditMetrics;
