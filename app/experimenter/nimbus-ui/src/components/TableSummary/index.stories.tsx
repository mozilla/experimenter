/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";
import AppLayout from "../AppLayout";
import TableSummary from ".";
import { RouterSlugProvider } from "../../lib/test-utils";

storiesOf("components/TableSummary", module)
  .add("all fields filled out", () => {
    const { data } = mockExperimentQuery("demo-slug", {
      featureConfig: MOCK_CONFIG.featureConfig![1],
    });
    return (
      <Subject>
        <TableSummary experiment={data!} />
      </Subject>
    );
  })
  .add("filled out with multiple probe sets", () => {
    const { data } = mockExperimentQuery("demo-slug", {
      featureConfig: MOCK_CONFIG.featureConfig![1],
      primaryProbeSets: [
        {
          __typename: "NimbusProbeSetType",
          id: "1",
          slug: "picture_in_picture",
          name: "Picture-in-Picture",
        },
        {
          __typename: "NimbusProbeSetType",
          id: "2",
          slug: "feature_C",
          name: "Feature C",
        },
      ],
      secondaryProbeSets: [
        {
          __typename: "NimbusProbeSetType",
          id: "1",
          slug: "feature_b",
          name: "Feature B",
        },
        {
          __typename: "NimbusProbeSetType",
          id: "2",
          slug: "feature_d",
          name: "Feature D",
        },
      ],
    });
    return (
      <Subject>
        <TableSummary experiment={data!} />
      </Subject>
    );
  })
  .add("only required fields filled out", () => {
    const { data } = mockExperimentQuery("demo-slug", {
      primaryProbeSets: [],
      secondaryProbeSets: [],
    });
    return (
      <Subject>
        <TableSummary experiment={data!} />
      </Subject>
    );
  })
  .add("missing required fields", () => {
    const { data } = mockExperimentQuery("demo-slug", {
      primaryProbeSets: [],
      secondaryProbeSets: [],
      publicDescription: null,
    });

    return (
      <Subject>
        <TableSummary experiment={data!} />
      </Subject>
    );
  });

const Subject = ({ children }: { children: React.ReactElement }) => (
  <AppLayout>
    <RouterSlugProvider>{children}</RouterSlugProvider>
  </AppLayout>
);
