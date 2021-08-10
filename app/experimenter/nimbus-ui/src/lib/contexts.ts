/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { AnalysisData } from "./visualization/types";
import { getSortedBranches } from "./visualization/utils";

export type ResultsContextType = {
  analysis: AnalysisData;
  sortedBranches: ReturnType<typeof getSortedBranches>;
};

export const defaultResultsContext = {
  analysis: {
    daily: [],
    weekly: {},
    overall: {},
    metadata: { metrics: {}, outcomes: {} },
    show_analysis: false,
  },
  sortedBranches: [],
};

export const ResultsContext = React.createContext<ResultsContextType>(
  defaultResultsContext,
);
