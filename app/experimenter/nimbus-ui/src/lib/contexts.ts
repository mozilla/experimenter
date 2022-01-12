/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { ApolloError } from "@apollo/client";
import React from "react";
import { AsyncStateStatus } from "react-async-hook";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import { getStatus } from "./experiment";
import { AnalysisData } from "./visualization/types";
import { getSortedBranchNames } from "./visualization/utils";

export type ResultsContextType = {
  analysis: AnalysisData;
  sortedBranchNames: ReturnType<typeof getSortedBranchNames>;
  controlBranchName: string;
};

export const defaultResultsContext = {
  analysis: {
    daily: [],
    weekly: {},
    overall: {},
    metadata: { metrics: {}, outcomes: {}, external_config: null },
    show_analysis: false,
  },
  sortedBranchNames: [],
  controlBranchName: "",
};

export const ResultsContext = React.createContext<ResultsContextType>(
  defaultResultsContext,
);

export type ExperimentContextType = {
  slug: string;
  loading: boolean;
  error: ApolloError | undefined;
  status: ReturnType<typeof getStatus>;
  notFound: boolean;
  experiment: getExperiment_experimentBySlug;
  fetchAnalysis: (slugs: string[]) => void;
  analysis: AnalysisData | undefined;
  analysisFetchStatus: AsyncStateStatus;
  analysisError: Error | undefined;
  refetch: () => Promise<unknown>;
  startPolling: (pollInterval: number) => void;
  stopPolling: () => void;
};

export const ExperimentContext = React.createContext<
  ExperimentContextType | undefined
>(undefined);
