/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import AppLayoutWithExperiment from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";

export const Subject = ({ sidebar = true }: { sidebar?: boolean }) => {
  const { mock } = mockExperimentQuery("demo-slug");
  return (
    <RouterSlugProvider mocks={[mock]}>
      <AppLayoutWithExperiment
        title="Howdy!"
        testId="AppLayoutWithExperiment"
        {...{ sidebar }}
      >
        <p>Howdy neighbor</p>
      </AppLayoutWithExperiment>
    </RouterSlugProvider>
  );
};
