/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import AppLayoutSidebarLaunched from ".";
import { mockExperimentQuery, mockGetStatus } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import {
  mockAnalysis,
  MOCK_METADATA_WITH_CONFIG,
} from "../../lib/visualization/mocks";
import { AnalysisData } from "../../lib/visualization/types";
import { NimbusExperimentStatusEnum } from "../../types/globalTypes";

const Subject = ({
  analysisLoadingInSidebar,
  analysisError,
  analysis,
}: {
  analysisLoadingInSidebar?: boolean;
  analysisError?: Error;
  analysis?: AnalysisData;
}) => {
  const { experiment } = mockExperimentQuery("demo-slug");
  return (
    <RouterSlugProvider>
      <AppLayoutSidebarLaunched
        status={mockGetStatus({ status: NimbusExperimentStatusEnum.LIVE })}
        {...{ analysisLoadingInSidebar, experiment, analysisError, analysis }}
      >
        <p>App contents go here</p>
      </AppLayoutSidebarLaunched>
    </RouterSlugProvider>
  );
};

export default {
  title: "components/AppLayoutSidebarLaunched",
  component: Subject,
  decorators: [withLinks],
};

const storyWithProps = (
  props: React.ComponentProps<typeof Subject>,
  storyName?: string,
) => {
  const story = () => <Subject {...props} />;
  if (storyName) story.storyName = storyName;
  return story;
};

export const AnalysisResultsLoading = storyWithProps({
  analysisLoadingInSidebar: true,
});

export const AnalysisResultsError = storyWithProps({
  analysisError: new Error("Boop"),
});

export const AnalysisSkipped = storyWithProps({
  analysis: {
    show_analysis: true,
    daily: null,
    weekly: null,
    overall: null,
    metadata: MOCK_METADATA_WITH_CONFIG,
  },
});

export const AnalysisNotReady = storyWithProps({
  analysis: {
    show_analysis: true,
    daily: null,
    weekly: null,
    overall: null,
  },
});

export const AnalysisReady = storyWithProps({
  analysis: mockAnalysis(),
});
