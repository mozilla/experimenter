/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { withLinks } from "@storybook/addon-links";
import { RouterSlugProvider } from "../../lib/test-utils";
import { MockedCache, mockExperimentQuery } from "../../lib/mocks";
import PageEditOverview from ".";

const { mock } = mockExperimentQuery();

storiesOf("pages/EditOverview", module)
  .addDecorator(withLinks)
  .add("basic", () => (
    <RouterSlugProvider>
      <MockedCache mocks={[mock]}>
        <PageEditOverview />
      </MockedCache>
    </RouterSlugProvider>
  ));
