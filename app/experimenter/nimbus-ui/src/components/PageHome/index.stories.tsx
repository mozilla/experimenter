/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import PageHome from ".";
import { mockDirectoryExperimentsQuery, MockedCache } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";

export default {
  title: "pages/Home",
  component: PageHome,
  decorators: [withLinks],
};

export const Basic = () => (
  <RouterSlugProvider mocks={[mockDirectoryExperimentsQuery()]}>
    <PageHome />
  </RouterSlugProvider>
);

export const Loading = () => (
  <RouterSlugProvider mocks={[]}>
    <PageHome />
  </RouterSlugProvider>
);

export const NoExperiments = () => (
  <MockedCache mocks={[mockDirectoryExperimentsQuery([])]}>
    <PageHome />
  </MockedCache>
);

export const OnlyDrafts = () => (
  <MockedCache
    mocks={[
      mockDirectoryExperimentsQuery([
        { status: NimbusExperimentStatus.DRAFT },
        { status: NimbusExperimentStatus.DRAFT },
        { status: NimbusExperimentStatus.DRAFT },
        { status: NimbusExperimentStatus.DRAFT },
      ]),
    ]}
  >
    <PageHome />
  </MockedCache>
);
