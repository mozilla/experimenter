/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import AppLayoutSidebarLocked from ".";
import {
  MockAnalysisContextProvider,
  MockExperimentContextProvider,
} from "../../lib/mocks";
import { getExperiment } from "../../types/getExperiment";

export const Subject = ({
  experiment = {},
  analysis = {},
  loadingSidebar = false,
  analysisError,
}: {
  experiment?: Partial<getExperiment["experimentBySlug"]>;
  analysis?: Record<string, any> | null;
  loadingSidebar?: boolean;
  analysisError?: Error;
}) => (
  <MockExperimentContextProvider overrides={experiment}>
    <MockAnalysisContextProvider
      {...{ loadingSidebar, overrides: analysis, error: analysisError }}
    >
      <AppLayoutSidebarLocked>
        <p>Howdy neighbor</p>
      </AppLayoutSidebarLocked>
    </MockAnalysisContextProvider>
  </MockExperimentContextProvider>
);
