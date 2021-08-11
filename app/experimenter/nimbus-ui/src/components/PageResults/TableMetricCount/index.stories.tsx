/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import TableMetricCount from ".";
import { mockExperimentQuery, mockOutcomeSets } from "../../../lib/mocks";
import { GROUP, METRIC_TYPE } from "../../../lib/visualization/constants";
import { mockAnalysis } from "../../../lib/visualization/mocks";
import { getSortedBranches } from "../../../lib/visualization/utils";

const results = mockAnalysis();
const sortedBranches = getSortedBranches(results);

storiesOf("pages/Results/TableMetricCount", module)
  .addDecorator(withLinks)
  .add("with positive secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      secondaryOutcomes: ["picture_in_picture"],
    });
    const { secondaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <TableMetricCount
        {...{ results, sortedBranches }}
        outcomeSlug={secondaryOutcomes![0]!.slug!}
        outcomeDefaultName={secondaryOutcomes![0]!.friendlyName!}
        group={GROUP.OTHER}
        metricType={METRIC_TYPE.USER_SELECTED_SECONDARY}
      />
    );
  })
  .add("with negative secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    const { secondaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <TableMetricCount
        {...{ results, sortedBranches }}
        outcomeSlug={secondaryOutcomes![0]!.slug!}
        outcomeDefaultName={secondaryOutcomes![0]!.friendlyName!}
        group={GROUP.OTHER}
        metricType={METRIC_TYPE.USER_SELECTED_SECONDARY}
      />
    );
  })
  .add("with neutral secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      secondaryOutcomes: ["feature_c"],
    });
    const { secondaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <TableMetricCount
        {...{ results, sortedBranches }}
        outcomeSlug={secondaryOutcomes![0]!.slug!}
        outcomeDefaultName={secondaryOutcomes![0]!.friendlyName!}
        group={GROUP.OTHER}
        metricType={METRIC_TYPE.USER_SELECTED_SECONDARY}
      />
    );
  });
