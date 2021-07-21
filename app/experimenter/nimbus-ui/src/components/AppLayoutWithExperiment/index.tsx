/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { navigate, RouteComponentProps, useParams } from "@reach/router";
import React, { useEffect } from "react";
import { useAnalysis, useExperiment } from "../../hooks";
import { BASE_PATH } from "../../lib/constants";
import { getStatus, StatusCheck } from "../../lib/experiment";
import { AnalysisData } from "../../lib/visualization/types";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import ApolloErrorAlert from "../ApolloErrorAlert";
import AppLayoutSidebarLaunched from "../AppLayoutSidebarLaunched";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import Head from "../Head";
import HeaderExperiment from "../HeaderExperiment";
import PageExperimentNotFound from "../PageExperimentNotFound";
import PageLoading from "../PageLoading";

type AppLayoutWithExperimentChildrenProps = {
  experiment: getExperiment_experimentBySlug;
  refetch: () => Promise<unknown>;
  analysis?: AnalysisData;
};

export type RedirectCheck = {
  status: StatusCheck;
  review?: {
    ready: boolean;
    invalidPages: string[];
  };
  analysis?: AnalysisData;
  analysisError?: Error;
};

type AppLayoutWithExperimentProps = {
  children: (
    props: AppLayoutWithExperimentChildrenProps,
  ) => React.ReactNode | null;
  testId: string;
  title?: string;
  polling?: boolean;
  analysisRequired?: boolean; // the page and sidebar need analysis data
  analysisRequiredInSidebar?: boolean; // only the sidebar needs analysis data
  setHead?: boolean; // set the browser tab title through this component
  redirect?: ({
    status,
    analysis,
    analysisError,
  }: RedirectCheck) => string | void;
} & RouteComponentProps;

export const POLL_INTERVAL = 30000;

const AppLayoutWithExperiment = ({
  children,
  testId,
  title,
  polling = false,
  analysisRequired = false,
  analysisRequiredInSidebar = false,
  setHead = true,
  redirect,
}: AppLayoutWithExperimentProps) => {
  const { slug } = useParams();
  const {
    experiment,
    notFound,
    loading,
    startPolling,
    stopPolling,
    refetch,
    error,
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
  const analysisLoadingInSidebar = analysisRequiredInSidebar && analysisLoading;

  // If the redirect prop function is supplied let's call it with
  // experiment status, and analysis details. If it returns
  // a string we know to redirect to it as a path.
  let redirectPath: string | undefined, redirectResult: string | void;
  if (
    !loading &&
    redirect &&
    (redirectResult = redirect!({ status, analysis })) != null
  ) {
    redirectResult = redirectResult.length
      ? `/${redirectResult}`
      : redirectResult;
    redirectPath = `${BASE_PATH}/${slug}${redirectResult}`;
  }

  useEffect(() => {
    if (redirectPath) {
      navigate(redirectPath, { replace: true });
    }
  }, [redirectPath]);

  useEffect(() => {
    if (!analysisFetched && !loading && status.launched) {
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

  if (error) {
    return <ApolloErrorAlert {...{ error }} />;
  }

  // If the analysis is required for the sidebar and page, show the loader
  // until experiment data and analysis data have finished fetching
  if (loading || (analysisRequired && (!analysisFetched || analysisLoading))) {
    return <PageLoading />;
  }

  if (notFound) {
    return <PageExperimentNotFound {...{ slug }} />;
  }

  const { name, startDate, computedEndDate, computedDurationDays } = experiment;

  return (
    <Layout
      {...{
        children,
        analysisRequired,
        analysis,
        analysisLoadingInSidebar,
        analysisError,
        status,
        experiment,
      }}
    >
      <section data-testid={testId} id={testId}>
        {setHead && (
          <Head
            title={title ? `${experiment.name} – ${title}` : experiment.name}
          />
        )}

        <HeaderExperiment
          {...{
            slug,
            name,
            startDate,
            computedEndDate,
            status,
            computedDurationDays,
          }}
        />
        {title && <h2 className="mt-3 mb-4 h3">{title}</h2>}
        <div className="my-4">
          {children({ experiment, refetch, analysis })}
        </div>
      </section>
    </Layout>
  );
};

type LayoutProps = {
  children: React.ReactElement;
  status: StatusCheck;
  analysis?: AnalysisData;
  analysisRequired: boolean;
  analysisLoadingInSidebar: boolean;
  analysisError?: Error;
  experiment: getExperiment_experimentBySlug;
};

const Layout = ({
  children,
  status,
  analysis,
  analysisRequired,
  analysisLoadingInSidebar,
  analysisError,
  experiment,
}: LayoutProps) =>
  status?.launched ? (
    <AppLayoutSidebarLaunched
      {...{
        status,
        analysis,
        analysisRequired,
        analysisLoadingInSidebar,
        analysisError,
        experiment,
      }}
    >
      {children}
    </AppLayoutSidebarLaunched>
  ) : (
    <AppLayoutWithSidebar {...{ experiment }}>{children}</AppLayoutWithSidebar>
  );

export default AppLayoutWithExperiment;
