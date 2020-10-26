/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps, useParams } from "@reach/router";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import { useExperiment } from "../../hooks";

type PageEditOverviewProps = {} & RouteComponentProps;

const PageEditOverview = (props: PageEditOverviewProps) => {
  const { slug } = useParams();
  const { experiment } = useExperiment(slug);

  if (experiment != null) {
    console.log(
      experiment.hypothesis,
      experiment.application,
      experiment.publicDescription,
    );
  }

  return (
    <AppLayoutWithSidebar>
      <section data-testid="PageEditOverview">
        <h1>PageEditOverview</h1>
      </section>
    </AppLayoutWithSidebar>
  );
};

export default PageEditOverview;
