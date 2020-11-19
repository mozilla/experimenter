/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { RouterSlugProvider } from "../../lib/test-utils";
import { withLinks } from "@storybook/addon-links";
import { mockExperimentQuery } from "../../lib/mocks";
import TableVisualizationRow from ".";
import { mockAnalysis } from "../../lib/visualization/mocks";
import {
  DISPLAY_TYPE,
  BRANCH_COMPARISON,
  TABLE_LABEL,
} from "../../lib/visualization/constants";

const { mock } = mockExperimentQuery("demo-slug");

storiesOf("visualization/TableVisualizationRow", module)
  .addDecorator(withLinks)
  .add("Population field", () => (
    <RouterSlugProvider mocks={[mock]}>
      <TableVisualizationRow
        key="retained"
        results={mockAnalysis().overall.control}
        tableLabel={TABLE_LABEL.HIGHLIGHTS}
        metricKey="retained"
        displayType={DISPLAY_TYPE.POPULATION}
      />
    </RouterSlugProvider>
  ))
  .add("Count field", () => (
    <RouterSlugProvider mocks={[mock]}>
      <TableVisualizationRow
        key="retained"
        results={mockAnalysis().overall.control}
        tableLabel={TABLE_LABEL.HIGHLIGHTS}
        metricKey="retained"
        displayType={DISPLAY_TYPE.COUNT}
      />
    </RouterSlugProvider>
  ))
  .add("Percent field", () => (
    <RouterSlugProvider mocks={[mock]}>
      <TableVisualizationRow
        key="retained"
        results={mockAnalysis().overall.control}
        tableLabel={TABLE_LABEL.RESULTS}
        metricKey="retained"
        displayType={DISPLAY_TYPE.PERCENT}
      />
    </RouterSlugProvider>
  ))
  .add("Conversion count field", () => {
    const MOCK_ANALYSIS = mockAnalysis();
    return (
      <RouterSlugProvider mocks={[mock]}>
        <TableVisualizationRow
          key={DISPLAY_TYPE.CONVERSION_COUNT}
          branchComparison={BRANCH_COMPARISON.ABSOLUTE}
          displayType={DISPLAY_TYPE.CONVERSION_COUNT}
          results={MOCK_ANALYSIS.overall.treatment}
          tableLabel={TABLE_LABEL.PRIMARY_METRICS}
          metricKey="picture_in_picture_ever_used"
        />
      </RouterSlugProvider>
    );
  })
  .add("Conversion change field (positive)", () => {
    const MOCK_ANALYSIS = mockAnalysis();
    return (
      <RouterSlugProvider mocks={[mock]}>
        <TableVisualizationRow
          key={DISPLAY_TYPE.CONVERSION_COUNT}
          branchComparison={BRANCH_COMPARISON.UPLIFT}
          displayType={DISPLAY_TYPE.CONVERSION_CHANGE}
          results={MOCK_ANALYSIS.overall.treatment}
          tableLabel={TABLE_LABEL.PRIMARY_METRICS}
          metricKey="picture_in_picture_ever_used"
        />
      </RouterSlugProvider>
    );
  })
  .add("Conversion change field (negative)", () => {
    const MOCK_ANALYSIS = mockAnalysis();
    return (
      <RouterSlugProvider mocks={[mock]}>
        <TableVisualizationRow
          key={DISPLAY_TYPE.CONVERSION_COUNT}
          branchComparison={BRANCH_COMPARISON.UPLIFT}
          displayType={DISPLAY_TYPE.CONVERSION_CHANGE}
          results={MOCK_ANALYSIS.overall.treatment}
          tableLabel={TABLE_LABEL.PRIMARY_METRICS}
          metricKey="feature_b_ever_used"
        />
      </RouterSlugProvider>
    );
  })
  .add("Conversion change field (neutral)", () => {
    const MOCK_ANALYSIS = mockAnalysis();
    return (
      <RouterSlugProvider mocks={[mock]}>
        <TableVisualizationRow
          key={DISPLAY_TYPE.CONVERSION_COUNT}
          branchComparison={BRANCH_COMPARISON.UPLIFT}
          displayType={DISPLAY_TYPE.CONVERSION_CHANGE}
          results={MOCK_ANALYSIS.overall.treatment}
          tableLabel={TABLE_LABEL.PRIMARY_METRICS}
          metricKey="feature_c_ever_used"
        />
      </RouterSlugProvider>
    );
  });
