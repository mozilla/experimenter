/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import AppLayoutSidebarLocked from ".";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { mockAnalysis } from "../../lib/visualization/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";

const { experiment } = mockExperimentQuery("demo-slug");

storiesOf("components/AppLayoutSidebarLocked", module)
  .addDecorator(withLinks)
  .add("analysis results loading", () => (
    <RouterSlugProvider>
      <AppLayoutSidebarLocked
        status={mockGetStatus(NimbusExperimentStatus.LIVE)}
        analysisError={undefined}
        analysisLoadingInSidebar
        primaryProbeSets={null}
        secondaryProbeSets={null}
      >
        <p>App contents go here</p>
      </AppLayoutSidebarLocked>
    </RouterSlugProvider>
  ))
  .add("analysis results error", () => (
    <RouterSlugProvider>
      <AppLayoutSidebarLocked
        status={mockGetStatus(NimbusExperimentStatus.LIVE)}
        analysisError={new Error("Boop")}
        primaryProbeSets={null}
        secondaryProbeSets={null}
      >
        <p>App contents go here</p>
      </AppLayoutSidebarLocked>
    </RouterSlugProvider>
  ))
  .add("has analysis results", () => (
    <RouterSlugProvider>
      <AppLayoutSidebarLocked
        status={mockGetStatus(NimbusExperimentStatus.COMPLETE)}
        analysisError={undefined}
        analysis={{
          show_analysis: true,
          daily: [],
          weekly: {},
          overall: {},
          other_metrics: mockAnalysis().other_metrics,
        }}
        primaryProbeSets={experiment.primaryProbeSets}
        secondaryProbeSets={experiment.secondaryProbeSets}
      >
        <p>App contents go here</p>
      </AppLayoutSidebarLocked>
    </RouterSlugProvider>
  ));
