/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import HeaderExperiment from ".";
import { MockExperimentContextProvider } from "../../lib/mocks";
import { getExperiment } from "../../types/getExperiment";
import AppLayout from "../AppLayout";

export const Subject = ({
  experiment: overrides,
}: {
  experiment?: Partial<getExperiment["experimentBySlug"]>;
}) => (
  <MockExperimentContextProvider {...{ overrides }}>
    <AppLayout>
      <HeaderExperiment />
    </AppLayout>
  </MockExperimentContextProvider>
);
