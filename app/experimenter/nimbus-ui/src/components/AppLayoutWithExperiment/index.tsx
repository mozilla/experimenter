/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect } from "react";
import { RouteComponentProps, useParams } from "@reach/router";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import HeaderEditExperiment from "../HeaderEditExperiment";
import PageLoading from "../PageLoading";
import PageExperimentNotFound from "../PageExperimentNotFound";
import { useExperiment } from "../../hooks";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import AppLayout from "../AppLayout";

type AppLayoutWithExperimentChildrenProps = {
  experiment: getExperiment_experimentBySlug;
};

type AppLayoutWithExperimentProps = {
  children: (
    props: AppLayoutWithExperimentChildrenProps,
  ) => React.ReactNode | null;
  testId: string;
  title: string;
  polling?: boolean;
  sidebar?: boolean;
} & RouteComponentProps;

export const POLL_INTERVAL = 30000;

const AppLayoutWithExperiment = ({
  children,
  testId,
  title,
  sidebar = true,
  polling = false,
}: AppLayoutWithExperimentProps) => {
  const { slug } = useParams();
  const {
    experiment,
    notFound,
    loading,
    startPolling,
    stopPolling,
    review,
  } = useExperiment(slug);

  useEffect(() => {
    if (polling && experiment) {
      startPolling(POLL_INTERVAL);
    }
    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling, experiment, polling]);

  if (loading) {
    return <PageLoading />;
  }

  if (notFound) {
    return <PageExperimentNotFound {...{ slug }} />;
  }

  const { name, status } = experiment;

  return (
    <Layout {...{ sidebar, children, review }}>
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
    </Layout>
  );
};

const Layout = ({
  sidebar,
  children,
  review,
}: {
  sidebar: boolean;
  children: React.ReactElement;
  review: {
    ready: boolean;
    invalidPages: string[];
  };
}) =>
  sidebar ? (
    <AppLayoutWithSidebar {...{ review }}>{children}</AppLayoutWithSidebar>
  ) : (
    <AppLayout>{children}</AppLayout>
  );

export default AppLayoutWithExperiment;
