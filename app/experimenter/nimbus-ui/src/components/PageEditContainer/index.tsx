/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps, useParams } from "@reach/router";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import HeaderEditExperiment from "../HeaderEditExperiment";
import PageLoading from "../PageLoading";
import PageExperimentNotFound from "../PageExperimentNotFound";
import { useExperiment } from "../../hooks";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

type PageEditContainerChildrenProps = {
  experiment: getExperiment_experimentBySlug;
};

type PageEditContainerProps = {
  children: (props: PageEditContainerChildrenProps) => React.ReactNode | null;
  testId: string;
  title: string;
} & RouteComponentProps;

const PageEditContainer = ({
  children,
  testId,
  title,
}: PageEditContainerProps) => {
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
      <section data-testid={testId}>
        <HeaderEditExperiment
          {...{
            slug,
            name,
            status,
          }}
        />
        <h2 className="mt-3 mb-4 h4" data-testid="page-title">
          {title}
        </h2>
        {children({ experiment })}
      </section>
    </AppLayoutWithSidebar>
  );
};

export default PageEditContainer;
