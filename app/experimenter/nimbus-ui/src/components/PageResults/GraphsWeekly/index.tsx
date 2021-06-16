/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
import React, { useState } from "react";
import Collapse from "react-bootstrap/Collapse";
import vegaEmbed, { VisualizationSpec } from "vega-embed";
import { ReactComponent as CollapseMinus } from "../../../images/minus.svg";
import { ReactComponent as ExpandPlus } from "../../../images/plus.svg";
import {
  BRANCH_COMPARISON,
  BRANCH_COMPARISON_TITLE,
} from "../../../lib/visualization/constants";
import { lineGraphConfig } from "../../../lib/visualization/graphConfig";
import {
  AnalysisDataWeekly,
  BranchDescription,
  FormattedAnalysisPoint,
} from "../../../lib/visualization/types";

const getGraphID = (outcomeSlug: string, branchComparison: string) =>
  `${outcomeSlug}_${branchComparison}_graph`;

/**
 * We should only graph if there are at least 2 weeks of data
 * because otherwise the graph is just a single point and useless.
 *
 * So we return empty mergedBranchData to avoid graphing when there
 * isn't enough data
 */
const getMergedBranchData = (
  outcomeSlug: string,
  group: string,
  weeklyResults: { [branch: string]: BranchDescription },
) => {
  const mergedBranchData: { [graphID: string]: FormattedAnalysisPoint[] } = {};
  let maxWeeks = 0;
  Object.keys(weeklyResults).forEach((branch: string) => {
    if (outcomeSlug in weeklyResults[branch].branch_data[group]) {
      Object.values(BRANCH_COMPARISON).forEach((branchComparison) => {
        const graphID = getGraphID(outcomeSlug, branchComparison);
        const branchData =
          weeklyResults[branch].branch_data[group][outcomeSlug][
            branchComparison
          ].all;
        branchData.forEach((dataPoint: FormattedAnalysisPoint) => {
          dataPoint["branch"] = branch;
          const weekIndex: number =
            "window_index" in dataPoint ? dataPoint["window_index"]! : 0;
          if (weekIndex > maxWeeks) {
            maxWeeks = weekIndex;
          }
        });
        const updatedBranchData = mergedBranchData[graphID] || [];
        mergedBranchData[graphID] = updatedBranchData.concat(branchData);
      });
    }
  });

  return maxWeeks === 1 ? {} : mergedBranchData;
};

const embedGraphs = (
  outcomeSlug: string,
  outcomeName: string,
  mergedBranchData: { [graphID: string]: FormattedAnalysisPoint[] },
) => {
  let branchComparisonKey: keyof typeof BRANCH_COMPARISON;
  for (branchComparisonKey in BRANCH_COMPARISON) {
    const branchComparison = BRANCH_COMPARISON[branchComparisonKey];
    const graphID = getGraphID(outcomeSlug, branchComparison);
    const branchComparisonTitle = BRANCH_COMPARISON_TITLE[branchComparisonKey];
    const title = `Mean ${outcomeName} Per User (${branchComparisonTitle})`;
    const mergedBranchComparisonData =
      graphID in mergedBranchData ? mergedBranchData[graphID] : [];

    if (mergedBranchComparisonData.length > 0) {
      const spec = lineGraphConfig(
        mergedBranchComparisonData,
        title,
      ) as VisualizationSpec;
      vegaEmbed(`#${graphID}`, spec, { actions: false });
    }
  }
};

type GraphsWeeklyProps = {
  weeklyResults: AnalysisDataWeekly;
  outcomeSlug: string;
  outcomeName: string;
  group: string;
};

const GraphsWeekly = ({
  weeklyResults = {},
  outcomeSlug,
  outcomeName,
  group,
}: GraphsWeeklyProps) => {
  const mergedBranchData = getMergedBranchData(
    outcomeSlug,
    group,
    weeklyResults,
  );

  const [open, setOpen] = useState(false);
  const [embedded, setEmbedded] = useState(false);
  const graphsVisibleClass = !open ? "d-none" : "";
  const graphsHiddenClass = open ? "d-none" : "";

  const handleCollapse = () => {
    setOpen(!open);
    if (!embedded) {
      embedGraphs(outcomeSlug, outcomeName, mergedBranchData);
    }
    setEmbedded(true);
  };

  return (
    <>
      {Object.keys(mergedBranchData).length > 0 && (
        <>
          <span
            onClick={handleCollapse}
            aria-controls="graphs"
            aria-expanded={open}
            className="text-primary btn"
          >
            <ExpandPlus className={graphsHiddenClass} />
            <CollapseMinus className={graphsVisibleClass} />{" "}
            <span className={graphsHiddenClass}>Show Graphs</span>
            <span className={graphsVisibleClass}>Hide Graphs</span>
          </span>
          <Collapse in={open}>
            <div id="graphs">
              <div id={`${outcomeSlug}_absolute_graph`} className="w-100" />
              <div id={`${outcomeSlug}_difference_graph`} className="w-100" />
              <div
                id={`${outcomeSlug}_relative_uplift_graph`}
                className="w-100"
              />
            </div>
          </Collapse>
        </>
      )}
    </>
  );
};

export default GraphsWeekly;
