/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import TableMetricSecondary from ".";
import { useOutcomes } from "../../../hooks/useOutcomes";
import { mockExperimentQuery } from "../../../lib/mocks";
import { mockAnalysis } from "../../../lib/visualization/mocks";

storiesOf("pages/Results/TableMetricSecondary", module)
  .addDecorator(withLinks)
  .add("with positive secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      secondaryOutcomes: ["picture_in_picture"],
    });
    const { secondaryOutcomes } = useOutcomes(experiment);

    return (
      <TableMetricSecondary
        results={mockAnalysis()}
        outcomeSlug={secondaryOutcomes![0]!.slug!}
        outcomeDefaultName={secondaryOutcomes![0]!.friendlyName!}
        isDefault={false}
      />
    );
  })
  .add("with negative secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    const { secondaryOutcomes } = useOutcomes(experiment);

    return (
      <TableMetricSecondary
        results={mockAnalysis()}
        outcomeSlug={secondaryOutcomes![0]!.slug!}
        outcomeDefaultName={secondaryOutcomes![0]!.friendlyName!}
        isDefault={false}
      />
    );
  })
  .add("with neutral secondary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      secondaryOutcomes: ["feature_c"],
    });
    const { secondaryOutcomes } = useOutcomes(experiment);

    return (
      <TableMetricSecondary
        results={mockAnalysis()}
        outcomeSlug={secondaryOutcomes![0]!.slug!}
        outcomeDefaultName={secondaryOutcomes![0]!.friendlyName!}
        isDefault={false}
      />
    );
  });
