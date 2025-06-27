/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import TableVisualizationRow from "src/components/PageResults/TableVisualizationRow";
import {
  BRANCH_COMPARISON,
  DISPLAY_TYPE,
  TABLE_LABEL,
} from "src/lib/visualization/constants";
import { BranchDescription } from "src/lib/visualization/types";

describe("TableVisualizationRow", () => {
  it("doesn't crash on undefined lower/upper values", () => {
    const branchResults: BranchDescription = {
      is_control: false,
      branch_data: {
        other_metrics: {
          identity: {
            absolute: {
              first: { point: 1.2 },
              all: [{ point: 1.2 }],
            },
            difference: {
              control: {
                first: { point: 1.2 },
                all: [{ point: 1.2 }],
              },
              treatment: {
                first: { point: 1.2 },
                all: [{ point: 1.2 }],
              },
            },
            relative_uplift: {
              control: {
                first: { point: 1.2 },
                all: [{ point: 1.2 }],
              },
              treatment: {
                first: { point: 1.2 },
                all: [{ point: 1.2 }],
              },
            },
          },
        },
      },
    };

    const displayType = DISPLAY_TYPE.COUNT;
    const branchComparison = BRANCH_COMPARISON.ABSOLUTE;
    const group = "other_metrics";
    const metricKey = "identity";
    const bounds = 1;

    render(
      <TableVisualizationRow
        results={branchResults}
        tableLabel={TABLE_LABEL.SECONDARY_METRICS}
        metricKey={metricKey}
        {...{
          displayType,
          branchComparison,
          bounds,
          group,
        }}
        isControlBranch={false}
        referenceBranch={"control"}
      />,
    );

    expect(screen.queryAllByText("undefined to undefined")).toHaveLength(1);
  });
});
