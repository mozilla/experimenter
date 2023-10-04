/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { ComponentType } from "react";
import { Tab, Tabs } from "react-bootstrap";
import { TableHighlightsProps } from "src/components/PageResults/TableHighlights";
import { TableResultsProps } from "src/components/PageResults/TableResults";
import { TableResultsWeeklyProps } from "src/components/PageResults/TableResultsWeekly";
import { BRANCH_COMPARISON } from "src/lib/visualization/constants";
import { AnalysisBases } from "src/lib/visualization/types";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

type TablesWithExperiment =
  | ComponentType<TableHighlightsProps>
  | ComponentType<TableResultsProps>;

type TablesWithoutExperiment = ComponentType<TableResultsWeeklyProps>;

export type TableWithTabComparisonProps = {
  experiment?: getExperiment_experimentBySlug;
  Table: TablesWithExperiment | TablesWithoutExperiment;
  className?: string;
  analysisBasis?: AnalysisBases;
  segment?: string;
  isDesktop?: boolean;
};

export const TableWithTabComparison = ({
  experiment,
  Table,
  className = "rounded-bottom mb-5",
  analysisBasis = "enrollments",
  segment = "all",
  isDesktop = false,
}: TableWithTabComparisonProps) => (
  <Tabs defaultActiveKey={BRANCH_COMPARISON.UPLIFT} className="border-bottom-0">
    <Tab eventKey={BRANCH_COMPARISON.UPLIFT} title="Relative uplift comparison">
      <div className={`border ${className}`}>
        {experiment ? (
          <Table
            {...{ experiment }}
            analysisBasis={analysisBasis}
            segment={segment}
          />
        ) : (
          /* @ts-ignore - TODO, assert Table is TablesWithoutExperiment if `experiment` not provided */
          <Table
            analysisBasis={analysisBasis}
            segment={segment}
            isDesktop={isDesktop}
          />
        )}
      </div>
    </Tab>
    <Tab eventKey={BRANCH_COMPARISON.ABSOLUTE} title="Absolute comparison">
      <div className={`border ${className}`}>
        {experiment ? (
          <Table
            {...{ experiment }}
            branchComparison={BRANCH_COMPARISON.ABSOLUTE}
            analysisBasis={analysisBasis}
            segment={segment}
          />
        ) : (
          <>
            {/* @ts-ignore - TODO, assert Table is TablesWithoutExperiment if `experiment` not provided */}
            <Table
              branchComparison={BRANCH_COMPARISON.ABSOLUTE}
              analysisBasis={analysisBasis}
              segment={segment}
              isDesktop={isDesktop}
            />
          </>
        )}
      </div>
    </Tab>
  </Tabs>
);

export default TableWithTabComparison;
