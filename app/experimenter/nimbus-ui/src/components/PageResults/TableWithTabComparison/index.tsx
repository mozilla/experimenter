/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { ComponentType } from "react";
import { Tab, Tabs } from "react-bootstrap";
import { BRANCH_COMPARISON } from "../../../lib/visualization/constants";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import { TableHighlightsProps } from "../TableHighlights";
import { TableResultsProps } from "../TableResults";
import { TableResultsWeeklyProps } from "../TableResultsWeekly";

type TablesWithExperiment =
  | ComponentType<TableHighlightsProps>
  | ComponentType<TableResultsProps>;

type TablesWithoutExperiment = ComponentType<TableResultsWeeklyProps>;

export type TableWithTabComparisonProps = {
  experiment?: getExperiment_experimentBySlug;
  Table: TablesWithExperiment | TablesWithoutExperiment;
  className?: string;
};

export const TableWithTabComparison = ({
  experiment,
  Table,
  className = "rounded-bottom mb-5",
}: TableWithTabComparisonProps) => (
  <Tabs defaultActiveKey={BRANCH_COMPARISON.UPLIFT} className="border-bottom-0">
    <Tab eventKey={BRANCH_COMPARISON.UPLIFT} title="Relative uplift comparison">
      <div className={`border ${className}`}>
        {/* @ts-ignore - TODO, assert Table is TablesWithoutExperiment if `experiment` not provided */}
        {experiment ? <Table {...{ experiment }} /> : <Table />}
      </div>
    </Tab>
    <Tab eventKey={BRANCH_COMPARISON.ABSOLUTE} title="Absolute comparison">
      <div className={`border ${className}`}>
        {experiment ? (
          <Table
            {...{ experiment }}
            branchComparison={BRANCH_COMPARISON.ABSOLUTE}
          />
        ) : (
          <>
            {/* @ts-ignore - TODO, assert Table is TablesWithoutExperiment if `experiment` not provided */}
            <Table branchComparison={BRANCH_COMPARISON.ABSOLUTE} />
          </>
        )}
      </div>
    </Tab>
  </Tabs>
);

export default TableWithTabComparison;
