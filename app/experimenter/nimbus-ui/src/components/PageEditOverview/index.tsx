/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";

type PageEditOverviewProps = {} & RouteComponentProps;

const PageEditOverview = (props: PageEditOverviewProps) => (
  <AppLayoutWithSidebar>
    <section data-testid="PageEditOverview">
      <h1>PageEditOverview</h1>
    </section>
  </AppLayoutWithSidebar>
);

export default PageEditOverview;
