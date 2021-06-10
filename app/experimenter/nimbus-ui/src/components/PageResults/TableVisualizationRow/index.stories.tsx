/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { storiesOf } from "@storybook/react";
import React from "react";
import TableVisualizationRow from ".";
import {
  BRANCH_COMPARISON,
  DISPLAY_TYPE,
  GROUP,
  TABLE_LABEL,
} from "../../../lib/visualization/constants";
import {
  mockAnalysis,
  mockIncompleteAnalysis,
} from "../../../lib/visualization/mocks";

const MOCK_ANALYSIS = mockAnalysis();
const MOCK_INCOMPLETE_ANALYSIS = mockIncompleteAnalysis();

storiesOf("pages/Results/TableVisualizationRow", module)
  .addDecorator(withLinks)
  .add("Population field", () => (
    <TableVisualizationRow
      results={MOCK_ANALYSIS.overall.control}
      tableLabel={TABLE_LABEL.HIGHLIGHTS}
      metricKey="retained"
      displayType={DISPLAY_TYPE.POPULATION}
      group={GROUP.OTHER}
    />
  ))
  .add("Count field", () => (
    <TableVisualizationRow
      results={MOCK_ANALYSIS.overall.control}
      tableLabel={TABLE_LABEL.HIGHLIGHTS}
      metricKey="retained"
      displayType={DISPLAY_TYPE.COUNT}
      group={GROUP.OTHER}
    />
  ))
  .add("Percent field", () => (
    <TableVisualizationRow
      results={MOCK_ANALYSIS.overall.control}
      tableLabel={TABLE_LABEL.RESULTS}
      metricKey="retained"
      displayType={DISPLAY_TYPE.PERCENT}
      group={GROUP.OTHER}
    />
  ))
  .add("Conversion count field", () => (
    <TableVisualizationRow
      branchComparison={BRANCH_COMPARISON.ABSOLUTE}
      displayType={DISPLAY_TYPE.CONVERSION_COUNT}
      results={MOCK_ANALYSIS.overall.treatment}
      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
      metricKey="picture_in_picture_ever_used"
      group={GROUP.OTHER}
    />
  ))
  .add("Conversion change field (positive)", () => (
    <TableVisualizationRow
      branchComparison={BRANCH_COMPARISON.UPLIFT}
      displayType={DISPLAY_TYPE.CONVERSION_CHANGE}
      results={MOCK_ANALYSIS.overall.treatment}
      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
      metricKey="picture_in_picture_ever_used"
      group={GROUP.OTHER}
    />
  ))
  .add("Conversion change field (negative)", () => (
    <TableVisualizationRow
      branchComparison={BRANCH_COMPARISON.UPLIFT}
      displayType={DISPLAY_TYPE.CONVERSION_CHANGE}
      results={MOCK_ANALYSIS.overall.treatment}
      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
      metricKey="feature_b_ever_used"
      group={GROUP.OTHER}
    />
  ))
  .add("Conversion change field (neutral)", () => (
    <TableVisualizationRow
      branchComparison={BRANCH_COMPARISON.UPLIFT}
      displayType={DISPLAY_TYPE.CONVERSION_CHANGE}
      results={MOCK_ANALYSIS.overall.treatment}
      tableLabel={TABLE_LABEL.PRIMARY_METRICS}
      metricKey="feature_c_ever_used"
      group={GROUP.OTHER}
    />
  ))
  .add("Count field missing values", () => (
    <TableVisualizationRow
      results={MOCK_INCOMPLETE_ANALYSIS.overall.control}
      metricName="Retention"
      tableLabel={TABLE_LABEL.RESULTS}
      metricKey="retained"
      displayType={DISPLAY_TYPE.PERCENT}
      group={GROUP.OTHER}
    />
  ));
