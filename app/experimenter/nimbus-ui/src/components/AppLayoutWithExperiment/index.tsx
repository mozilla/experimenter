/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect, useState } from "react";
import { navigate, RouteComponentProps, useParams } from "@reach/router";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import HeaderExperiment from "../HeaderExperiment";
import PageLoading from "../PageLoading";
import PageExperimentNotFound from "../PageExperimentNotFound";
import { useAnalysis, useExperiment, ExperimentReview } from "../../hooks";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import AppLayout from "../AppLayout";
import { AnalysisData } from "../../lib/visualization/types";
import Head from "../Head";
import { getStatus, StatusCheck } from "../../lib/experiment";
import { BASE_PATH } from "../../lib/constants";

type AppLayoutWithExperimentChildrenProps = {
  experiment: getExperiment_experimentBySlug;
  review: ExperimentReview;
  analysis?: AnalysisData;
};

type AppLayoutWithExperimentProps = {
  children: (
    props: AppLayoutWithExperimentChildrenProps,
  ) => React.ReactNode | null;
  testId: string;
  title?: string;
  polling?: boolean;
  sidebar?: boolean;
  analysisRequired?: boolean;
  redirect?: ({
    status,
    review,
    analysis,
  }: {
    status: StatusCheck;
    review?: {
      ready: boolean;
      invalidPages: string[];
    };
    analysis?: AnalysisData;
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
  } = useExperiment(slug);
  const { execute: fetchAnalysis, result: analysis } = useAnalysis();
  const [analysisFetched, setAnalysisFetched] = useState<boolean>(false);
  const status = getStatus(experiment);

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
      setAnalysisFetched(true);
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

  if (loading || (analysisRequired && !analysis)) {
    return <PageLoading />;
  }

  if (notFound) {
    return <PageExperimentNotFound {...{ slug }} />;
  }

  const { name } = experiment;

  return (
    <Layout {...{ sidebar, children, review, analysis, status }}>
      <section data-testid={testId}>
        <Head
          title={title ? `${experiment.name} – ${title}` : experiment.name}
        />

        <HeaderExperiment
          {...{
            slug,
            name,
            status,
          }}
        />
        {title && (
          <h2 className="mt-3 mb-4 h4" data-testid="page-title">
            {title}
          </h2>
        )}
        <div className="mt-4">{children({ experiment, review, analysis })}</div>
      </section>
    </Layout>
  );
};

type LayoutProps = {
  sidebar: boolean;
  children: React.ReactElement;
  status: StatusCheck;
  review: ExperimentReview;
  analysis?: AnalysisData;
};

const Layout = ({ sidebar, children, review, status, analysis }: LayoutProps) =>
  sidebar ? (
    <AppLayoutWithSidebar {...{ status, review, analysis }}>
      {children}
    </AppLayoutWithSidebar>
  ) : (
    <AppLayout>{children}</AppLayout>
  );

export default AppLayoutWithExperiment;
