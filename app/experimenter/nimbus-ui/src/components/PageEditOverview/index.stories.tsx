/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { withQuery } from "@storybook/addon-queryparams";
import { storiesOf } from "@storybook/react";
import React from "react";
import PageEditOverview from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";

const { mock } = mockExperimentQuery("demo-slug");
const { mock: mockMissingFields } = mockExperimentQuery("demo-slug", {
  publicDescription: "",
  riskBrand: null,
  riskPartnerRelated: null,
  riskRevenue: null,
  readyForReview: {
    ready: false,
    message: {
      public_description: ["This field may not be null."],
      risk_brand: ["This field may not be null."],
      risk_revenue: ["This field may not be null."],
      risk_partner_related: ["This field may not be null."],
    },
  },
});

storiesOf("pages/EditOverview", module)
  .addDecorator(withLinks)
  .addDecorator(withQuery)
  .add("basic", () => (
    <RouterSlugProvider mocks={[mock]}>
      <PageEditOverview />
    </RouterSlugProvider>
  ))
  .add(
    "missing fields",
    () => (
      <RouterSlugProvider mocks={[mockMissingFields]}>
        <PageEditOverview />
      </RouterSlugProvider>
    ),
    {
      query: {
        "show-errors": true,
      },
    },
  );
