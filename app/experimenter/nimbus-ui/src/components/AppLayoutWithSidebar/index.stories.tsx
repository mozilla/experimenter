/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { withLinks } from "@storybook/addon-links";
import { RouterSlugProvider } from "../../lib/test-utils";
import AppLayoutWithSidebar from ".";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { mockGetStatus } from "../../lib/mocks";

storiesOf("components/AppLayoutWithSidebar", module)
  .addDecorator(withLinks)
  .add("basic", () => (
    <RouterSlugProvider>
      <AppLayoutWithSidebar>
        <p>App contents go here</p>
      </AppLayoutWithSidebar>
    </RouterSlugProvider>
  ))
  .add("missing details", () => (
    <RouterSlugProvider>
      <AppLayoutWithSidebar
        review={{
          ready: false,
          invalidPages: ["branches", "audience"],
        }}
      >
        <p>App contents go here</p>
      </AppLayoutWithSidebar>
    </RouterSlugProvider>
  ))
  .add("status: review", () => (
    <RouterSlugProvider>
      <AppLayoutWithSidebar
        status={mockGetStatus(NimbusExperimentStatus.REVIEW)}
      >
        <p>App contents go here</p>
      </AppLayoutWithSidebar>
    </RouterSlugProvider>
  ))
  .add("status: accepted", () => (
    <RouterSlugProvider>
      <AppLayoutWithSidebar
        status={mockGetStatus(NimbusExperimentStatus.ACCEPTED)}
      >
        <p>App contents go here</p>
      </AppLayoutWithSidebar>
    </RouterSlugProvider>
  ))
  .add("status: live", () => (
    <RouterSlugProvider>
      <AppLayoutWithSidebar status={mockGetStatus(NimbusExperimentStatus.LIVE)}>
        <p>App contents go here</p>
      </AppLayoutWithSidebar>
    </RouterSlugProvider>
  ));
