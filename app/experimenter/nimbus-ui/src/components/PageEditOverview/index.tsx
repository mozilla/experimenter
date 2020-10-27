/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps, useParams } from "@reach/router";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import { useExperiment } from "../../hooks";
import HeaderEditExperiment from "../HeaderEditExperiment";
import PageExperimentNotFound from "../PageExperimentNotFound";
import PageLoading from "../PageLoading";

type PageEditOverviewProps = {} & RouteComponentProps;

const PageEditOverview = (props: PageEditOverviewProps) => {
  const { slug } = useParams();
  const { experiment, notFound, loading } = useExperiment(slug);

  if (loading) {
    return <PageLoading />;
  }

  if (notFound) {
    return <PageExperimentNotFound {...{ slug }} />;
  }

  const { name, status } = experiment;
  return (
    <AppLayoutWithSidebar>
      <section data-testid="PageEditOverview">
        <HeaderEditExperiment
          {...{
            slug,
            name,
            status,
          }}
        />
        <h2 className="mt-3 h4">Overview</h2>
      </section>
    </AppLayoutWithSidebar>
  );
};

export default PageEditOverview;
