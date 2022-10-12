/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React, { useContext, useState } from "react";
import Collapse from "react-bootstrap/Collapse";
import { ReactComponent as CollapseMinus } from "../../../images/minus.svg";
import { ReactComponent as ExpandPlus } from "../../../images/plus.svg";
import { ResultsContext } from "../../../lib/contexts";
import {
  BRANCH_COMPARISON,
  GENERAL_TIPS,
  HIGHLIGHTS_METRICS_LIST,
} from "../../../lib/visualization/constants";
import { BranchComparisonValues } from "../../../lib/visualization/types";
import TableWeekly from "../TableWeekly";

export type TableResultsWeeklyProps = {
  branchComparison?: BranchComparisonValues;
  segment?: string;
};

const TableResultsWeekly = ({
  branchComparison = BRANCH_COMPARISON.UPLIFT,
  segment = "all",
}: TableResultsWeeklyProps) => {
  const {
    analysis: { overall },
  } = useContext(ResultsContext);
  const hasOverallResults = !!overall?.all;
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
          {HIGHLIGHTS_METRICS_LIST.map((metric, index) => {
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
