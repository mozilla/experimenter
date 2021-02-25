/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import PageSummary from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";

storiesOf("pages/Summary", module)
  .addDecorator(withLinks)
  .add("with draft experiment", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.DRAFT,
    });
    return (
      <RouterSlugProvider mocks={[mock]}>
        <PageSummary polling={false} />
      </RouterSlugProvider>
    );
  })
  .add("with preview experiment", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.PREVIEW,
    });
    return (
      <RouterSlugProvider mocks={[mock]}>
        <PageSummary polling={false} />
      </RouterSlugProvider>
    );
  })
  .add("with live experiment", () => {
    const { mock } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
    });
    return (
      <RouterSlugProvider mocks={[mock]}>
        <PageSummary polling={false} />
      </RouterSlugProvider>
    );
  });
