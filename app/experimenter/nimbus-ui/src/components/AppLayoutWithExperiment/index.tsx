/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { navigate, RouteComponentProps, useParams } from "@reach/router";
import React, { useEffect } from "react";
import { useAnalysis, useExperiment } from "../../hooks";
import { BASE_PATH } from "../../lib/constants";
import { AnalysisContext, ExperimentContext } from "../../lib/contexts";
import { getStatus, StatusCheck } from "../../lib/experiment";
import { AnalysisData } from "../../lib/visualization/types";
import AppLayout from "../AppLayout";
import AppLayoutSidebarLocked from "../AppLayoutSidebarLocked";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import Head from "../Head";
import HeaderExperiment from "../HeaderExperiment";
import PageExperimentNotFound from "../PageExperimentNotFound";
import PageLoading from "../PageLoading";

type AppLayoutWithExperimentProps = {
  children: React.ReactNode;
  testId: string;
  title?: string;
  polling?: boolean;
  sidebar?: boolean;
  analysisRequired?: boolean; // the page and sidebar need analysis data
  analysisRequiredInSidebar?: boolean; // only the sidebar needs analysis data
  redirect?: ({
    status,
    review,
    analysis,
    analysisError,
  }: {
    status: StatusCheck;
    review?: {
      ready: boolean;
      invalidPages: string[];
    };
    analysis?: AnalysisData;
    analysisError?: Error;
  }) => string | void;
} & RouteComponentProps;

export const POLL_INTERVAL = 30000;

const AppLayoutWithExperiment = ({
  children,
  testId,
  title,
  sidebar = true,
  polling = false,
  analysisRequired = false,
  analysisRequiredInSidebar = false,
  redirect,
}: AppLayoutWithExperimentProps) => {
  const { slug } = useParams();
  const {
    experiment,
    notFound,
    loading,
    startPolling,
    stopPolling,
    review,
    refetch,
  } = useExperiment(slug);
  const {
    execute: fetchAnalysis,
    result: analysis,
    error: analysisError,
    status: analysisFetchStatus,
  } = useAnalysis();
  const status = getStatus(experiment);
  const analysisLoading = analysisFetchStatus === "loading";
  const analysisFetched = analysisFetchStatus !== "not-requested";
  const analysisSidebarLoading = analysisRequiredInSidebar && analysisLoading;

  // If the redirect prop function is supplied let's call it with
  // experiment status, review, and analysis details. If it returns
  // a string we know to redirect to it as a path.
  let redirectPath: string | undefined, getRedirect: string | void;
  if (
    !loading &&
    redirect &&
    (getRedirect = redirect!({ status, review, analysis }))
  ) {
    redirectPath = `${BASE_PATH}/${slug}/${getRedirect}`;
  }

  useEffect(() => {
    if (redirectPath) {
      navigate(redirectPath, { replace: true });
    }
  }, [redirectPath]);

  useEffect(() => {
    if (!analysisFetched && !loading && status.locked) {
      fetchAnalysis([experiment?.slug]);
    }
  }, [fetchAnalysis, loading, experiment, analysisFetched, status]);

  useEffect(() => {
    if (polling && experiment) {
      startPolling(POLL_INTERVAL);
    }
    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling, experiment, polling]);

  // If the analysis is required for the sidebar and page, show the loader
  // until experiment data and analysis data have finished fetching
  if (loading || (analysisRequired && (!analysisFetched || analysisLoading))) {
    return <PageLoading />;
  }

  if (notFound) {
    return <PageExperimentNotFound {...{ slug }} />;
  }

  const experimentContext = {
    experiment,
    review,
    status,
    refetch,
  };

  const analysisContext = {
    analysis,
    loading: analysisLoading,
    loadingSidebar: analysisSidebarLoading,
    error: analysisError,
  };

  return (
    <ExperimentContext.Provider value={experimentContext}>
      <AnalysisContext.Provider value={analysisContext}>
        <Layout
          {...{
            sidebar,
            children,
            status,
          }}
        >
          <section data-testid={testId}>
            <Head
              title={title ? `${experiment.name} – ${title}` : experiment.name}
            />
            <HeaderExperiment />
            {title && (
              <h2 className="mt-3 mb-4 h4" data-testid="page-title">
                {title}
              </h2>
            )}
            <div className="my-4">{children}</div>
          </section>
        </Layout>
      </AnalysisContext.Provider>
    </ExperimentContext.Provider>
  );
};

type LayoutProps = {
  sidebar: boolean;
  children: React.ReactElement;
  status: StatusCheck;
};

const Layout = ({ sidebar, children, status }: LayoutProps) => {
  if (!sidebar) {
    return <AppLayout>{children}</AppLayout>;
  }

  return status?.locked ? (
    <AppLayoutSidebarLocked>{children}</AppLayoutSidebarLocked>
  ) : (
    <AppLayoutWithSidebar>{children}</AppLayoutWithSidebar>
  );
};

export default AppLayoutWithExperiment;
