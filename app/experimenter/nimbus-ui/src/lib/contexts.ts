/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { getExperiment_experimentBySlug } from "../types/getExperiment";
import {
  getReviewReadiness,
  getStatus,
  ReviewReadiness,
  StatusCheck,
} from "./experiment";
import { AnalysisData } from "./visualization/types";

export const ExperimentContext = React.createContext<{
  experiment?: getExperiment_experimentBySlug;
  refetch: () => void;
  status: StatusCheck;
  review: ReviewReadiness;
}>({
  refetch: () => {},
  status: getStatus(),
  review: getReviewReadiness(),
});

export const AnalysisContext = React.createContext<{
  analysis?: AnalysisData | null;
  error?: Error;
  loading?: boolean;
  loadingSidebar?: boolean;
}>({});
