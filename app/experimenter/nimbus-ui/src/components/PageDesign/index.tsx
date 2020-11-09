/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithSidebarAndData from "../AppLayoutWithSidebarAndData";

const PageDesign: React.FunctionComponent<RouteComponentProps> = () => {
  return (
    <AppLayoutWithSidebarAndData title="Design" testId="PageDesign">
      {({ experiment }) => <p>{experiment.name}</p>}
    </AppLayoutWithSidebarAndData>
  );
};

export default PageDesign;
