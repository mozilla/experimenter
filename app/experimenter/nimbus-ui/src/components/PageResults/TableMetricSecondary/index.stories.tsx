/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import TableMetricSecondary from ".";
import { mockExperimentQuery, mockOutcomeSets } from "../../../lib/mocks";
import { GROUP } from "../../../lib/visualization/constants";
import { mockAnalysis } from "../../../lib/visualization/mocks";
import { getSortedBranches } from "../../../lib/visualization/utils";

const results = mockAnalysis();
const sortedBranches = getSortedBranches(results);

storiesOf("pages/Results/TableMetricSecondary", module)
  .addDecorator(withLinks)
  .add("with positive secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      secondaryOutcomes: ["picture_in_picture"],
    });
    const { secondaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <TableMetricSecondary
        {...{ results, sortedBranches }}
        outcomeSlug={secondaryOutcomes![0]!.slug!}
        outcomeDefaultName={secondaryOutcomes![0]!.friendlyName!}
        group={GROUP.OTHER}
        isDefault={false}
      />
    );
  })
  .add("with negative secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    const { secondaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <TableMetricSecondary
        {...{ results, sortedBranches }}
        outcomeSlug={secondaryOutcomes![0]!.slug!}
        outcomeDefaultName={secondaryOutcomes![0]!.friendlyName!}
        group={GROUP.OTHER}
        isDefault={false}
      />
    );
  })
  .add("with neutral secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      secondaryOutcomes: ["feature_c"],
    });
    const { secondaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <TableMetricSecondary
        {...{ results, sortedBranches }}
        outcomeSlug={secondaryOutcomes![0]!.slug!}
        outcomeDefaultName={secondaryOutcomes![0]!.friendlyName!}
        group={GROUP.OTHER}
        isDefault={false}
      />
    );
  });
