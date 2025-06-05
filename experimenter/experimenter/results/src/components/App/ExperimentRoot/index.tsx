/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps, useMatch } from "@reach/router";
import React, { useEffect, useRef } from "react";
import PageLoading from "src/components/PageLoading";
import { useAnalysis, useExperiment } from "src/hooks";
import { BASE_PATH } from "src/lib/constants";
import { ExperimentContext, RedirectCondition } from "src/lib/contexts";
import { getStatus } from "src/lib/experiment";

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
  const useRedirectCondition = (redirect: RedirectCondition) => {};

  const useExperimentPolling = () => {};

  // If the analysis is required for the sidebar and page, show the loader
  // until experiment data and analysis data have finished fetching
  if (
    loading ||
    (analysisRequired.current && (!analysisFetched || analysisLoading))
  ) {
    return <PageLoading />;
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

export default ExperimentRoot;
