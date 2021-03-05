/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import TableMetricSecondary from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { mockAnalysis } from "../../../lib/visualization/mocks";

storiesOf("pages/Results/TableMetricSecondary", module)
  .addDecorator(withLinks)
  .add("with positive secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      secondaryOutcomes: [
        {
          slug: "picture_in_picture",
          name: "Picture-in-Picture",
        },
      ],
    });

    return (
      <TableMetricSecondary
        results={mockAnalysis()}
        probeSetSlug={experiment.secondaryOutcomes![0]!.slug}
        probeSetDefaultName={experiment.secondaryOutcomes![0]!.name}
        isDefault={false}
      />
    );
  })
  .add("with negative secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    return (
      <TableMetricSecondary
        results={mockAnalysis()}
        probeSetSlug={experiment.secondaryOutcomes![0]!.slug}
        probeSetDefaultName={experiment.secondaryOutcomes![0]!.name}
        isDefault={false}
      />
    );
  })
  .add("with neutral secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      secondaryOutcomes: [
        {
          slug: "feature_c",
          name: "Feature C",
        },
      ],
    });

    return (
      <TableMetricSecondary
        results={mockAnalysis()}
        probeSetSlug={experiment.secondaryOutcomes![0]!.slug}
        probeSetDefaultName={experiment.secondaryOutcomes![0]!.name}
        isDefault={false}
      />
    );
  });
