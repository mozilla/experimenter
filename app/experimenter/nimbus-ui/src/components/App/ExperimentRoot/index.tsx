/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { navigate, RouteComponentProps, useMatch } from "@reach/router";
import React, { useEffect, useRef } from "react";
import { useAnalysis, useExperiment } from "../../../hooks";
import { BASE_PATH, POLL_INTERVAL } from "../../../lib/constants";
import { ExperimentContext } from "../../../lib/contexts";
import { getStatus, StatusCheck } from "../../../lib/experiment";
import { AnalysisData } from "../../../lib/visualization/types";
import ApolloErrorAlert from "../../ApolloErrorAlert";
import PageExperimentNotFound from "../../PageExperimentNotFound";
import PageLoading from "../../PageLoading";

export const ExperimentRoot = ({
  // BASE_PATH is a constant in App, but some tests vary in RouterSlugProvider
  basepath = BASE_PATH,
  children,
}: {
  basepath?: string;
  children: React.ReactNode;
} & RouteComponentProps) => {
  // Should always find a slug route match, here.
  const { slug } = useMatch(`${basepath}/:slug/*`)!;

  const {
    experiment,
    notFound,
    loading,
    startPolling,
    stopPolling,
    refetch,
    error,
  } = useExperiment(slug);

  const status = getStatus(experiment);

  const {
    execute: fetchAnalysis,
    result: analysis,
    error: analysisError,
    status: analysisFetchStatus,
  } = useAnalysis();

  const polling = useRef(false);
  const analysisRequired = useRef(false);

  const analysisLoading = analysisFetchStatus === "loading";
  const analysisFetched = analysisFetchStatus !== "not-requested";
  const pollExperiment = Boolean(polling.current && experiment);
  // if an error occurs after the experiment data is present, it's a polling error
  const hasPollError = error && pollExperiment;

  // Attempt to fetch analysis for launched experiment happens on all pages.
  useEffect(() => {
    if (!analysisFetched && !loading && status.launched) {
      fetchAnalysis([experiment?.slug]);
    }
  }, [fetchAnalysis, loading, experiment, analysisFetched, status]);

  // When a page requires analysis (i.e. PageResults), this utility hook
  // enables the loading spinner until analysis fetch complete.
  const useAnalysisRequired = () => {
    useEffect(() => {
      analysisRequired.current = true;
      return () => {
        analysisRequired.current = false;
      };
    }, []);
  };

  // Utility to execute a redirect when condition is met, deferred until
  // after experiment has been loaded
  const useRedirectCondition = (redirect: RedirectCondition) => {
    let redirectPath: string | undefined, redirectResult: string | void;
    if (
      !loading &&
      status &&
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
  };

  // Utility hook to enable experiment polling (e.g. on PageSummary)
  const useExperimentPolling = () => {
    useEffect(() => {
      polling.current = true;
      startPolling(POLL_INTERVAL);
      return () => {
        polling.current = false;
        stopPolling();
      };
    }, []);
  };

  if (error && !hasPollError) {
    return <ApolloErrorAlert {...{ error }} />;
  }

  // If the analysis is required for the sidebar and page, show the loader
  // until experiment data and analysis data have finished fetching
  if (
    loading ||
    (analysisRequired.current && (!analysisFetched || analysisLoading))
  ) {
    return <PageLoading />;
  }

  if (notFound) {
    return <PageExperimentNotFound {...{ slug }} />;
  }

  return (
    <ExperimentContext.Provider
      value={{
        slug,
        status,
        experiment,
        analysis,
        analysisRequired: analysisRequired.current,
        analysisError,
        analysisLoading,
        refetch,
        hasPollError,
        polling: polling.current,
        useExperimentPolling,
        useRedirectCondition,
        useAnalysisRequired,
      }}
    >
      {children}
    </ExperimentContext.Provider>
  );
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

export type RedirectCondition = ({
  status,
  analysis,
  analysisError,
}: RedirectCheck) => string | void;

export default ExperimentRoot;
