/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import TableSummary from ".";
import { mockExperimentQuery, MOCK_CONFIG } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import AppLayout from "../../AppLayout";

storiesOf("components/Summary/TableSummary", module)
  .add("all fields filled out", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      featureConfig: MOCK_CONFIG.featureConfig![1],
    });
    return (
      <Subject>
        <TableSummary {...{ experiment }} />
      </Subject>
    );
  })
  .add("filled out with multiple probe sets", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      featureConfig: MOCK_CONFIG.featureConfig![1],
      primaryOutcomes: [
        {
          slug: "picture_in_picture",
          name: "Picture-in-Picture",
        },
        {
          slug: "feature_C",
          name: "Feature C",
        },
      ],
      secondaryOutcomes: [
        {
          slug: "feature_b",
          name: "Feature B",
        },
        {
          slug: "feature_d",
          name: "Feature D",
        },
      ],
    });
    return (
      <Subject>
        <TableSummary {...{ experiment }} />
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
        <TableSummary {...{ experiment }} />
      </Subject>
    );
  })
  .add("missing required fields", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: [],
      secondaryOutcomes: [],
      publicDescription: "",
      riskMitigationLink: "",
      documentationLinks: [],
    });

    return (
      <Subject>
        <TableSummary {...{ experiment }} />
      </Subject>
    );
  });

const Subject = ({ children }: { children: React.ReactElement }) => (
  <AppLayout>
    <RouterSlugProvider>{children}</RouterSlugProvider>
  </AppLayout>
);
