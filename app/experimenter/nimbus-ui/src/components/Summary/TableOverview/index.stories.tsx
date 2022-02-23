/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import TableOverview from ".";
import { mockExperimentQuery, MOCK_CONFIG } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import AppLayout from "../../AppLayout";

storiesOf("components/Summary/TableOverview", module)
  .add("all fields filled out", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      featureConfigs: [MOCK_CONFIG.allFeatureConfigs![1]],
    });
    return (
      <Subject>
        <TableOverview {...{ experiment }} />
      </Subject>
    );
  })
  .add("filled out with multiple outcomes", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      featureConfigs: [MOCK_CONFIG.allFeatureConfigs![1]],
      primaryOutcomes: ["picture_in_picture", "feature_C"],
      secondaryOutcomes: ["feature_b", "feature_d"],
    });
    return (
      <Subject>
        <TableOverview {...{ experiment }} />
      </Subject>
    );
  })
  .add("only required fields filled out", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: [],
      secondaryOutcomes: [],
      documentationLinks: [],
    });
    return (
      <Subject>
        <TableOverview {...{ experiment }} />
      </Subject>
    );
  })
  .add("missing required fields", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: [],
      secondaryOutcomes: [],
      publicDescription: "",
      riskRevenue: null,
      riskBrand: null,
      riskPartnerRelated: null,
      documentationLinks: [],
    });

    return (
      <Subject>
        <TableOverview {...{ experiment }} />
      </Subject>
    );
  });

const Subject = ({ children }: { children: React.ReactElement }) => (
  <AppLayout>
    <RouterSlugProvider>{children}</RouterSlugProvider>
  </AppLayout>
);
