/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import AppLayoutWithSidebar from ".";
import { mockGetStatus } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";

storiesOf("components/AppLayoutWithSidebar", module)
  .addDecorator(withLinks)
  .add("status: draft", () => (
    <RouterSlugProvider>
      <AppLayoutWithSidebar>
        <p>App contents go here</p>
      </AppLayoutWithSidebar>
    </RouterSlugProvider>
  ))
  .add("status: preview", () => (
    <RouterSlugProvider>
      <AppLayoutWithSidebar
        status={mockGetStatus({ status: NimbusExperimentStatus.PREVIEW })}
      >
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
  ));
