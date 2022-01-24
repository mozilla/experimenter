/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import { getStatus, StatusCheck } from "./experiment";
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

export type ExperimentContextType = {
  slug: string;
  status: ReturnType<typeof getStatus>;
  experiment: getExperiment_experimentBySlug;
  analysis?: AnalysisData;
  analysisLoading?: boolean;
  analysisError?: Error;
  refetch: () => Promise<unknown>;
  hasPollError?: boolean;
  useRedirectCondition: (redirect: RedirectCondition) => void;
  useExperimentPolling: () => void;
  useAnalysisRequired: () => void;
  polling: boolean;
  analysisRequired: boolean;
};

export const ExperimentContext = React.createContext<
  ExperimentContextType | undefined
>(undefined);
