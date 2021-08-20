/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import fetchMock from "fetch-mock";
import React from "react";
import PageResults from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import {
  mockAnalysis,
  MOCK_METADATA_WITH_CONFIG,
} from "../../lib/visualization/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";

const { mock } = mockExperimentQuery("demo-slug", {
  status: NimbusExperimentStatus.COMPLETE,
});

storiesOf("pages/Results", module)
  .addDecorator(withLinks)
  .add("basic", () => {
    fetchMock
      .restore()
      .getOnce("/api/v3/visualization/demo-slug/", mockAnalysis());
    return (
      <RouterSlugProvider mocks={[mock]}>
        <PageResults />
      </RouterSlugProvider>
    );
  })
  .add("with external config overrides", () => {
    fetchMock
      .restore()
      .getOnce(
        "/api/v3/visualization/demo-slug/",
        mockAnalysis({ metadata: MOCK_METADATA_WITH_CONFIG }),
      );
    return (
      <RouterSlugProvider mocks={[mock]}>
        <PageResults />
      </RouterSlugProvider>
    );
  });
