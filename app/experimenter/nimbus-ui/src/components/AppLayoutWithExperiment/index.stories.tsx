/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import AppLayoutWithExperiment from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";

const { mock } = mockExperimentQuery("demo-slug");

storiesOf("components/AppLayoutWithExperiment", module)
  .addDecorator(withLinks)
  .add("default", () => (
    <RouterSlugProvider mocks={[mock]}>
      <AppLayoutWithExperiment title="Howdy!" testId="AppLayoutWithExperiment">
        {({ experiment }) => <p>{experiment.name}</p>}
      </AppLayoutWithExperiment>
    </RouterSlugProvider>
  ));
