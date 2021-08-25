/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import fetchMock from "fetch-mock";
import React from "react";
import PageResults from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import {
  mockAnalysis,
  MOCK_METADATA,
  MOCK_METADATA_WITH_CONFIG,
  weeklyMockAnalysis,
} from "../../lib/visualization/mocks";
import { AnalysisData } from "../../lib/visualization/types";
import { NimbusExperimentStatus } from "../../types/globalTypes";

const Subject = ({
  analysis = mockAnalysis(),
}: {
  analysis?: AnalysisData;
}) => {
  const { mock } = mockExperimentQuery("demo-slug", {
    status: NimbusExperimentStatus.COMPLETE,
  });
  fetchMock.restore().getOnce("/api/v3/visualization/demo-slug/", analysis);
  return (
    <RouterSlugProvider mocks={[mock]}>
      <PageResults />
    </RouterSlugProvider>
  );
};

export default {
  title: "pages/Results",
  component: Subject,
  decorators: [withLinks],
};

const storyWithProps = (
  props?: React.ComponentProps<typeof Subject>,
  storyName?: string,
) => {
  const story = () => <Subject {...props} />;
  if (storyName) story.storyName = storyName;
  return story;
};

/*
 * If a control branch override exists in production, the branch values won't simply be swapped
 * as they are here because the analysis will be reran to produce new values based on the
 * new control branch. We're just swapping them here for Storybook representation.
 */
const analysisWithAllOverrides = () => {
  const weeklyAnalysis = weeklyMockAnalysis();
  const weeklyAnalysisWithBranchOverride = {
    control: weeklyAnalysis.treatment,
    treatment: weeklyAnalysis.control,
  };
  const analysis = mockAnalysis({
    metadata: MOCK_METADATA_WITH_CONFIG,
    weekly: weeklyAnalysisWithBranchOverride,
  });

  return {
    ...analysis,
    overall: {
      control: analysis.overall.treatment,
      treatment: analysis.overall.control,
    },
  };
};

export const Basic = storyWithProps();

export const WithOneExternalConfigOverride = storyWithProps({
  analysis: mockAnalysis({
    metadata: {
      ...MOCK_METADATA,
      external_config: {
        start_date: null,
        end_date: "2020-10-27",
        enrollment_period: null,
        reference_branch: null,
        skip: false,
        url: "#",
      },
    },
  }),
});

export const WithAllExternalConfigOverrides = storyWithProps({
  analysis: analysisWithAllOverrides(),
});
