/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import PageHome from ".";
import { mockDirectoryExperimentsQuery } from "../../lib/mocks";
import { CurrentLocation, RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";

interface StoryContext {
  args: {
    mocks: Parameters<typeof RouterSlugProvider>[0]["mocks"];
  };
}

const withRouterAndCurrentUrl = (
  Story: React.FC,
  { args: { mocks = [mockDirectoryExperimentsQuery()] } }: StoryContext,
) => (
  <RouterSlugProvider mocks={mocks}>
    <>
      <CurrentLocation />
      <Story />
    </>
  </RouterSlugProvider>
);

export default {
  title: "pages/Home",
  component: PageHome,
  decorators: [withRouterAndCurrentUrl, withLinks],
};

const storyTemplate = (mocks: StoryContext["args"]["mocks"]) => {
  return Object.assign(() => <PageHome />, { args: { mocks } });
};

export const Basic = storyTemplate([mockDirectoryExperimentsQuery()]);

export const Loading = storyTemplate([]);

export const NoExperiments = storyTemplate([mockDirectoryExperimentsQuery([])]);

export const OnlyDrafts = storyTemplate([
  mockDirectoryExperimentsQuery([
    { status: NimbusExperimentStatus.DRAFT },
    { status: NimbusExperimentStatus.DRAFT },
    { status: NimbusExperimentStatus.DRAFT },
    { status: NimbusExperimentStatus.DRAFT },
  ]),
]);
