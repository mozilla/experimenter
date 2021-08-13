/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import TableMetricConversion from ".";
import {
  mockExperimentQuery,
  mockOutcomeSets,
  MockResultsContextProvider,
} from "../../../lib/mocks";

storiesOf("pages/Results/TableMetricConversion", module)
  .addDecorator(withLinks)
  .add("with positive primary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: ["picture_in_picture"],
    });
    const { primaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <MockResultsContextProvider>
        <TableMetricConversion outcome={primaryOutcomes![0]!} />
      </MockResultsContextProvider>
    );
  })
  .add("with negative primary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: ["feature_b"],
    });
    const { primaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <MockResultsContextProvider>
        <TableMetricConversion outcome={primaryOutcomes![0]!} />
      </MockResultsContextProvider>
    );
  })
  .add("with neutral primary metric", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      primaryOutcomes: ["feature_c"],
    });
    const { primaryOutcomes } = mockOutcomeSets(experiment);

    return (
      <MockResultsContextProvider>
        <TableMetricConversion outcome={primaryOutcomes![0]!} />
      </MockResultsContextProvider>
    );
  });
