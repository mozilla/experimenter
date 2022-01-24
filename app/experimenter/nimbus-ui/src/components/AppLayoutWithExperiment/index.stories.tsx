/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import AppLayoutWithExperiment, { AppLayoutWithExperimentProps } from ".";
import { ExperimentContextType } from "../../lib/contexts";
import { mockExperimentQuery } from "../../lib/mocks";
import {
  MockExperimentContextProvider,
  RouterSlugProvider,
} from "../../lib/test-utils";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "../../types/globalTypes";

const Subject = ({
  context = {},
  ...props
}: {
  context?: Partial<ExperimentContextType>;
} & Omit<AppLayoutWithExperimentProps, "children">) => {
  return (
    <MockExperimentContextProvider value={context}>
      <AppLayoutWithExperiment title="Howdy!" {...props}>
        <p>Experiment goes here</p>
      </AppLayoutWithExperiment>
    </MockExperimentContextProvider>
  );
};

export default {
  title: "components/AppLayoutWithExperiment",
  component: Subject,
  decorators: [withLinks],
};

const storyWithProps = (
  { mock } = mockExperimentQuery("demo-slug"),
  props: React.ComponentProps<typeof Subject> = {},
  storyName?: string,
) => {
  const story = () => (
    <RouterSlugProvider mocks={[mock]}>
      <Subject {...props} />
    </RouterSlugProvider>
  );
  if (storyName) story.storyName = storyName;
  return story;
};

export const StatusDraft = storyWithProps();

export const StatusPreview = storyWithProps(
  mockExperimentQuery("demo-slug", {
    status: NimbusExperimentStatusEnum.PREVIEW,
  }),
);

export const StatusLaunched = storyWithProps(
  mockExperimentQuery("demo-slug", {
    status: NimbusExperimentStatusEnum.LIVE,
  }),
  {},
  'Status: Launched ("Live" or "Complete")',
);

export const PublishStatusReview = storyWithProps(
  mockExperimentQuery("demo-slug", {
    publishStatus: NimbusExperimentPublishStatusEnum.REVIEW,
  }),
);

export const PollingError = storyWithProps(
  mockExperimentQuery("demo-slug"),
  { context: { hasPollError: true } },
  "Polling error",
);
