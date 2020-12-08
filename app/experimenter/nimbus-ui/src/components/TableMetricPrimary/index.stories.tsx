/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { withLinks } from "@storybook/addon-links";
import { mockExperimentQuery } from "../../lib/mocks";
import TableMetricPrimary from ".";
import { mockAnalysis } from "../../lib/visualization/mocks";

storiesOf("visualization/TableMetricPrimary", module)
  .addDecorator(withLinks)
  .add("with positive primary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryProbeSets: [
        {
          __typename: "NimbusProbeSetType",
          id: "1",
          slug: "picture_in_picture",
          name: "Picture-in-Picture",
        },
      ],
    });

    return (
      <TableMetricPrimary
        results={mockAnalysis().overall}
        probeSet={experiment.primaryProbeSets![0]!}
      />
    );
  })
  .add("with negative primary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryProbeSets: [
        {
          __typename: "NimbusProbeSetType",
          id: "1",
          slug: "feature_b",
          name: "Feature B",
        },
      ],
    });

    return (
      <TableMetricPrimary
        results={mockAnalysis().overall}
        probeSet={experiment.primaryProbeSets![0]!}
      />
    );
  })
  .add("with neutral primary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryProbeSets: [
        {
          __typename: "NimbusProbeSetType",
          id: "1",
          slug: "feature_c",
          name: "Feature C",
        },
      ],
    });

    return (
      <TableMetricPrimary
        results={mockAnalysis().overall}
        probeSet={experiment.primaryProbeSets![0]!}
      />
    );
  });
