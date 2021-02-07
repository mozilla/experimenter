/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import TableSummary from ".";
import { MockExperimentContextProvider, MOCK_CONFIG } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { getExperiment } from "../../../types/getExperiment";
import AppLayout from "../../AppLayout";

storiesOf("components/Summary/TableSummary", module)
  .add("all fields filled out", () => (
    <Subject
      experiment={{
        featureConfig: MOCK_CONFIG.featureConfig![1],
      }}
    />
  ))
  .add("filled out with multiple probe sets", () => (
    <Subject
      experiment={{
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
      }}
    />
  ))
  .add("only required fields filled out", () => (
    <Subject
      experiment={{
        primaryProbeSets: [],
        secondaryProbeSets: [],
        documentationLinks: [],
      }}
    />
  ))
  .add("missing required fields", () => (
    <Subject
      experiment={{
        primaryProbeSets: [],
        secondaryProbeSets: [],
        publicDescription: "",
        riskMitigationLink: "",
        documentationLinks: [],
      }}
    />
  ));

const Subject = ({
  experiment: overrides = {},
}: {
  experiment?: Partial<getExperiment["experimentBySlug"]>;
}) => (
  <MockExperimentContextProvider {...{ overrides }}>
    <AppLayout>
      <RouterSlugProvider>
        <TableSummary />
      </RouterSlugProvider>
    </AppLayout>
  </MockExperimentContextProvider>
);
