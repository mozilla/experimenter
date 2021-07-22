/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import TableMetricConversion from ".";
import { mockExperimentQuery, mockOutcomeSets } from "../../../lib/mocks";
import { mockAnalysis } from "../../../lib/visualization/mocks";
import { getSortedBranches } from "../../../lib/visualization/utils";

const results = mockAnalysis().overall;
const sortedBranches = getSortedBranches(mockAnalysis());

storiesOf("pages/Results/TableMetricConversion", module)
  .addDecorator(withLinks)
  .add("with positive primary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: ["picture_in_picture"],
    });
    const { primaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <TableMetricConversion
        {...{ results, sortedBranches }}
        outcome={primaryOutcomes![0]!}
      />
    );
  })
  .add("with negative primary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: ["feature_b"],
    });
    const { primaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <TableMetricConversion
        {...{ results, sortedBranches }}
        outcome={primaryOutcomes![0]!}
      />
    );
  })
  .add("with neutral primary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: ["feature_c"],
    });
    const { primaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <TableMetricConversion
        {...{ results, sortedBranches }}
        outcome={primaryOutcomes![0]!}
      />
    );
  });
