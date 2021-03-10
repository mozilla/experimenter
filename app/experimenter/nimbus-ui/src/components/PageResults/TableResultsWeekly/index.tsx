/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
import React, { useState } from "react";
import Collapse from "react-bootstrap/Collapse";
import { ReactComponent as CollapseMinus } from "../../../images/minus.svg";
import { ReactComponent as ExpandPlus } from "../../../images/plus.svg";
import { GENERAL_TIPS } from "../../../lib/visualization/constants";
import { AnalysisDataWeekly } from "../../../lib/visualization/types";
import TableWeekly from "../TableWeekly";

type TableResultsWeeklyProps = {
  weeklyResults: AnalysisDataWeekly;
  hasOverallResults: boolean;
  metricsList: { value: string; name: string; tooltip: string }[];
};

const TableResultsWeekly = ({
  weeklyResults = {},
  hasOverallResults = false,
  metricsList,
}: TableResultsWeeklyProps) => {
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
        className="text-primary btn mb-5"
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
        <div className="ml-3">
          {metricsList.map((metric) => {
            return (
              <div key={`${metric.value}_weekly`}>
                <h3 className="h5 mb-3">{metric.name}</h3>
                <TableWeekly
                  metricKey={metric.value}
                  metricName={metric.name}
                  results={weeklyResults}
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
