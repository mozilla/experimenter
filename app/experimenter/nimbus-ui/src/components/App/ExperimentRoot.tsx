/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps, useMatch } from "@reach/router";
import React from "react";
import { useAnalysis, useExperiment } from "../../hooks";
import { BASE_PATH } from "../../lib/constants";
import { ExperimentContext } from "../../lib/contexts";
import { getStatus } from "../../lib/experiment";

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

  const experimentResult = useExperiment(slug);
  const {
    experiment,
    notFound,
    loading,
    startPolling,
    stopPolling,
    refetch,
    error,
  } = experimentResult;

  const status = getStatus(experiment);

  const analysisResult = useAnalysis();
  const {
    execute: fetchAnalysis,
    result: analysis,
    error: analysisError,
    status: analysisFetchStatus,
  } = analysisResult;

  return (
    <ExperimentContext.Provider
      value={{
        slug,
        loading,
        error,
        status,
        notFound,
        experiment,
        fetchAnalysis,
        analysis,
        analysisError,
        analysisFetchStatus,
        refetch,
        startPolling,
        stopPolling,
      }}
    >
      {children}
    </ExperimentContext.Provider>
  );
};

export default ExperimentRoot;
