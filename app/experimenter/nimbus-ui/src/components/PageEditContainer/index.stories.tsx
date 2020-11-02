/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { RouterSlugProvider } from "../../lib/test-utils";
import { withLinks } from "@storybook/addon-links";
import PageEditContainer from ".";
import { mockExperimentQuery } from "../../lib/mocks";

const { mock } = mockExperimentQuery("demo-slug");

storiesOf("pages/EditContainer", module)
  .addDecorator(withLinks)
  .add("basic", () => (
    <RouterSlugProvider mocks={[mock]}>
      <PageEditContainer title="Howdy!" testId="PageEditContainer">
        {({ experiment }) => <p>{experiment.name}</p>}
      </PageEditContainer>
    </RouterSlugProvider>
  ));
