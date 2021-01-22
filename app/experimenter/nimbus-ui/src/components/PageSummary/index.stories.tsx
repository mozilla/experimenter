/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import PageSummary from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";

const { mock } = mockExperimentQuery("demo-slug");

storiesOf("pages/Summary", module)
  .addDecorator(withLinks)
  .add("basic", () => (
    <RouterSlugProvider mocks={[mock]}>
      <PageSummary polling={false} />
    </RouterSlugProvider>
  ));
