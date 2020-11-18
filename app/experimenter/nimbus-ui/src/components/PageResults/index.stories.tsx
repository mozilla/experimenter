/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { RouterSlugProvider } from "../../lib/test-utils";
import { withLinks } from "@storybook/addon-links";
import { mockExperimentQuery } from "../../lib/mocks";
import PageResults from ".";
import fetchMock from "fetch-mock";
import { mockAnalysis } from "../../lib/visualization/mocks";

const { mock } = mockExperimentQuery("demo-slug");

storiesOf("pages/Results", module)
  .addDecorator(withLinks)
  .add("basic, analysis available", () => {
    fetchMock
      .restore()
      .getOnce("/api/v3/visualization/demo-slug/", mockAnalysis());
    return (
      <RouterSlugProvider mocks={[mock]}>
        <PageResults />
      </RouterSlugProvider>
    );
  })
  .add("analysis unavailable", () => {
    fetchMock
      .restore()
      .getOnce(
        "/api/v3/visualization/demo-slug/",
        mockAnalysis({ show_analysis: false }),
      );
    return (
      <RouterSlugProvider mocks={[mock]}>
        <PageResults />
      </RouterSlugProvider>
    );
  })
  .add("analysis fetch errors", () => {
    fetchMock.restore().getOnce("/api/v3/visualization/demo-slug/", 500);
    return (
      <RouterSlugProvider mocks={[mock]}>
        <PageResults />
      </RouterSlugProvider>
    );
  });
