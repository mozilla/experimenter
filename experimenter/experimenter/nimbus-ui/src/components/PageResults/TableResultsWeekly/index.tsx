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

export type TableResultsWeeklyProps = {
  branchComparison?: BranchComparisonValues;
  analysisBasis?: AnalysisBases;
  segment?: string;
  isDesktop?: boolean;
};

const getHighlightMetrics = (isDesktop = false) => {
  // Make a copy of `HIGHLIGHTS_METRICS_LIST` since we modify it.
  if (isDesktop) {
    const highlightMetricsList = [...HIGHLIGHTS_METRICS_LIST];
    return highlightMetricsList.map((highlightMetric) => {
      if (highlightMetric.value === METRIC.DAYS_OF_USE) {
        return {
          value: METRIC.QUALIFIED_CUMULATIVE_DAYS_OF_USE,
          name: "Qualified Cumulative Days of Use",
          tooltip: METRICS_TIPS.QUALIFIED_CUMULATIVE_DAYS_OF_USE,
          group: METRIC_TO_GROUP[METRIC.QUALIFIED_CUMULATIVE_DAYS_OF_USE],
        };
      }
      return highlightMetric;
    });
  }

  return HIGHLIGHTS_METRICS_LIST;
};

const TableResultsWeekly = ({
  branchComparison = BRANCH_COMPARISON.UPLIFT,
  analysisBasis = "enrollments",
  segment = "all",
  isDesktop = false,
}: TableResultsWeeklyProps) => {
  const {
    analysis: { overall },
  } = useContext(ResultsContext);
  const hasOverallResults = !!overall?.[analysisBasis]?.all;
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
          {getHighlightMetrics(isDesktop).map((metric, index) => {
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
