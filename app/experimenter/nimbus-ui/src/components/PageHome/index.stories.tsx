/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { RouterSlugProvider } from "../../lib/test-utils";
import { withLinks } from "@storybook/addon-links";
import { mockDirectoryExperimentsQuery, MockedCache } from "../../lib/mocks";
import PageHome from ".";
import { NimbusExperimentStatus } from "../../types/globalTypes";

storiesOf("pages/Home", module)
  .addDecorator(withLinks)
  .add("basic", () => {
    return (
      <RouterSlugProvider mocks={[mockDirectoryExperimentsQuery()]}>
        <PageHome />
      </RouterSlugProvider>
    );
  })
  .add("loading", () => {
    return (
      <RouterSlugProvider mocks={[]}>
        <PageHome />
      </RouterSlugProvider>
    );
  })
  .add("no experiments", () => {
    return (
      <MockedCache mocks={[mockDirectoryExperimentsQuery([])]}>
        <PageHome />
      </MockedCache>
    );
  })
  .add("only drafts", () => {
    return (
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
  });
