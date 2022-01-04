/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import AppLayoutWithExperiment, { AppLayoutWithExperimentProps } from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import {
  NimbusExperimentPublishStatusEnum,
  NimbusExperimentStatusEnum,
} from "../../types/globalTypes";

const Subject = ({
  ...props
}: Omit<AppLayoutWithExperimentProps, "children">) => (
  <AppLayoutWithExperiment title="Howdy!" {...props}>
    {({ experiment }) => <p>{experiment.name}</p>}
  </AppLayoutWithExperiment>
);

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
  {
    polling: true,
    pollInterval: 2000,
  },
  "Polling error (wait 2 seconds)",
);
