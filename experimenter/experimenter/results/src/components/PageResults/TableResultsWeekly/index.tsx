/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React, { useContext, useState } from "react";
import Collapse from "react-bootstrap/Collapse";
import TableWeekly from "src/components/PageResults/TableWeekly";
import { ReactComponent as CollapseMinus } from "src/images/minus.svg";
import { ReactComponent as ExpandPlus } from "src/images/plus.svg";
import { ResultsContext } from "src/lib/contexts";
import {
  BRANCH_COMPARISON,
  GENERAL_TIPS,
  HIGHLIGHTS_METRICS_LIST,
  METRIC,
  METRICS_TIPS,
  METRIC_TO_GROUP,
} from "src/lib/visualization/constants";
import {
  AnalysisBases,
  BranchComparisonValues,
} from "src/lib/visualization/types";
import { shouldUseDou } from "src/lib/visualization/utils";

export type TableResultsWeeklyProps = {
  branchComparison?: BranchComparisonValues;
  analysisBasis?: AnalysisBases;
  segment?: string;
  referenceBranch: string;
};

const getHighlightMetrics = (useDou: boolean) => {
  // Make a copy of `HIGHLIGHTS_METRICS_LIST` since we modify it.
  let highlightMetricsList = [...HIGHLIGHTS_METRICS_LIST];
  if (useDou) {
    highlightMetricsList = highlightMetricsList.map((metric) => {
      if (metric.value === METRIC.DAILY_ACTIVE_USERS) {
        return {
          value: METRIC.DAYS_OF_USE,
          name: "Days of Use",
          tooltip: METRICS_TIPS.DAYS_OF_USE,
          group: METRIC_TO_GROUP[METRIC.DAYS_OF_USE],
        };
      }
      return metric;
    });
  }

  return highlightMetricsList;
};

const TableResultsWeekly = ({
  branchComparison = BRANCH_COMPARISON.UPLIFT,
  analysisBasis = "enrollments",
  segment = "all",
  referenceBranch,
}: TableResultsWeeklyProps) => {
  const {
    analysis: { overall, weekly },
  } = useContext(ResultsContext);
  const hasOverallResults = !!overall?.[analysisBasis]?.all;
  const hasWeeklyResults = !!weekly?.[analysisBasis]?.all;
  const useDou =
    hasWeeklyResults &&
    shouldUseDou(weekly![analysisBasis]?.[segment]![referenceBranch]);
  const [open, setOpen] = useState(!hasOverallResults);

  return (
    <>
      {!hasOverallResults && (
        <p className="p-3 mb-2 bg-warning text-dark">
          {GENERAL_TIPS.EARLY_RESULTS}
        </p>
      )}
      <span
        onClick={() => {
          setOpen(!open);
        }}
        aria-controls="weekly"
        aria-expanded={open}
        className="text-primary btn mb-3 mt-2"
      >
        {open ? (
          <>
            <CollapseMinus /> Hide Weekly Data
          </>
        ) : (
          <>
            <ExpandPlus /> Show Weekly Data
          </>
        )}
      </span>
      <Collapse in={open}>
        <div className="mt-2">
          {getHighlightMetrics(useDou).map((metric, index) => {
            return (
              <div key={`${metric.value}_weekly`}>
                <h3
                  className={classNames(
                    "h5",
                    "mb-3",
                    "ml-3",
                    index === 0 ? "mt-0" : "mt-4",
                  )}
                >
                  {metric.name}
                </h3>
                <TableWeekly
                  metricKey={metric.value}
                  metricName={metric.name}
                  group={metric.group}
                  {...{ branchComparison }}
                  analysisBasis={analysisBasis}
                  segment={segment}
                  referenceBranch={referenceBranch}
                />
              </div>
            );
          })}
        </div>
      </Collapse>
    </>
  );
};

export default TableResultsWeekly;
