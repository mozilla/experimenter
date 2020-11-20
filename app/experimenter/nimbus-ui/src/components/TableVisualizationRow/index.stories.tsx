/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { withLinks } from "@storybook/addon-links";
import TableVisualizationRow from ".";
import { mockAnalysis } from "../../lib/visualization/mocks";
import {
  DISPLAY_TYPE,
  BRANCH_COMPARISON,
  TABLE_LABEL,
} from "../../lib/visualization/constants";

const MOCK_ANALYSIS = mockAnalysis();

storiesOf("visualization/TableVisualizationRow", module)
  .addDecorator(withLinks)
  .add("Population field", () => (
    <TableVisualizationRow
      results={MOCK_ANALYSIS.overall.control}
      tableLabel={TABLE_LABEL.HIGHLIGHTS}
      metricKey="retained"
      displayType={DISPLAY_TYPE.POPULATION}
    />
  ))
  .add("Count field", () => (
    <TableVisualizationRow
      results={MOCK_ANALYSIS.overall.control}
      tableLabel={TABLE_LABEL.HIGHLIGHTS}
      metricKey="retained"
      displayType={DISPLAY_TYPE.COUNT}
    />
  ))
  .add("Percent field", () => (
    <TableVisualizationRow
      results={MOCK_ANALYSIS.overall.control}
      tableLabel={TABLE_LABEL.RESULTS}
      metricKey="retained"
      displayType={DISPLAY_TYPE.PERCENT}
    />
  ))
  .add("Conversion count field", () => (
    <TableVisualizationRow
      branchComparison={BRANCH_COMPARISON.ABSOLUTE}
      displayType={DISPLAY_TYPE.CONVERSION_COUNT}
      results={MOCK_ANALYSIS.overall.treatment}
      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
      metricKey="picture_in_picture_ever_used"
    />
  ))
  .add("Conversion change field (positive)", () => (
    <TableVisualizationRow
      branchComparison={BRANCH_COMPARISON.UPLIFT}
      displayType={DISPLAY_TYPE.CONVERSION_CHANGE}
      results={MOCK_ANALYSIS.overall.treatment}
      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
      metricKey="picture_in_picture_ever_used"
    />
  ))
  .add("Conversion change field (negative)", () => (
    <TableVisualizationRow
      branchComparison={BRANCH_COMPARISON.UPLIFT}
      displayType={DISPLAY_TYPE.CONVERSION_CHANGE}
      results={MOCK_ANALYSIS.overall.treatment}
      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
      metricKey="feature_b_ever_used"
    />
  ))
  .add("Conversion change field (neutral)", () => (
    <TableVisualizationRow
      branchComparison={BRANCH_COMPARISON.UPLIFT}
      displayType={DISPLAY_TYPE.CONVERSION_CHANGE}
      results={MOCK_ANALYSIS.overall.treatment}
      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
      metricKey="feature_c_ever_used"
    />
  ));
