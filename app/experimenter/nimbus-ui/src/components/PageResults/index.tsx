/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useState } from "react";
import Collapse from "react-bootstrap/Collapse";
import { useConfig } from "../../hooks";
import { ReactComponent as CollapseMinus } from "../../images/minus.svg";
import { ReactComponent as ExpandPlus } from "../../images/plus.svg";
import { ResultsContext, ResultsContextType } from "../../lib/contexts";
import {
  BRANCH_COMPARISON,
  GROUP,
  HIGHLIGHTS_METRICS_LIST,
  METRIC_TYPE,
} from "../../lib/visualization/constants";
import { BranchComparisonValues } from "../../lib/visualization/types";
import {
  analysisUnavailable,
  getControlBranchName,
  getSortedBranchNames,
} from "../../lib/visualization/utils";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import LinkExternal from "../LinkExternal";
import LinkMonitoring from "../LinkMonitoring";
import TableHighlights from "./TableHighlights";
import TableHighlightsOverview from "./TableHighlightsOverview";
import TableMetricCount from "./TableMetricCount";
import TableResults from "./TableResults";
import TableResultsWeekly from "./TableResultsWeekly";

const PageResults: React.FunctionComponent<RouteComponentProps> = () => {
  const { outcomes: configOutcomes } = useConfig();
  const groupStates: { [group: string]: any } = {
    usage_metrics: useState(true),
    search_metrics: useState(true),
    other_metrics: useState(true),
  };

  // show relative comparison by default
  // TODO: expand this functionality to other tables, EXP-1551
  const [branchComparison, setBranchComparison] =
    useState<BranchComparisonValues>(BRANCH_COMPARISON.UPLIFT);
  const branchComparisonIsRelative =
    branchComparison === BRANCH_COMPARISON.UPLIFT;
  const toggleBranchComparison = () => {
    if (branchComparisonIsRelative) {
      setBranchComparison(BRANCH_COMPARISON.ABSOLUTE);
    } else {
      setBranchComparison(BRANCH_COMPARISON.UPLIFT);
    }
  };
  const toggleBranchComparisonText = branchComparisonIsRelative
    ? "absolute"
    : "relative";

  return (
    <AppLayoutWithExperiment
      title="Analysis"
      testId="PageResults"
      analysisRequired
      redirect={({ status, analysis }) => {
        if (!status?.launched) {
          return "edit/overview";
        }

        if (analysisUnavailable(analysis)) {
          // Return to the experiment root/summary page
          return "";
        }
      }}
    >
      {({ experiment, analysis }) => {
        // For testing - users will be redirected if the analysis is unavailable
        // before reaching this return, but tests reach this return and
        // analysis.overall is expected to be an object (EXP-800)
        if (!analysis || analysisUnavailable(analysis)) return;

        const resultsContextValue: ResultsContextType = {
          analysis,
          sortedBranches: getSortedBranchNames(analysis),
          controlBranchName: getControlBranchName(analysis)!,
        };

        const slugUnderscored = experiment.slug.replace(/-/g, "_");

        return (
          <ResultsContext.Provider value={resultsContextValue}>
            <LinkMonitoring {...experiment} />
            <h3 className="h5 mb-3 mt-4" id="overview">
              Overview
            </h3>
            <p className="mb-4">
              Detailed analysis{" "}
              <LinkExternal
                href={`https://protosaur.dev/partybal/${slugUnderscored}.html`}
                data-testid="link-external-results"
              >
                can be found here
              </LinkExternal>
              .
            </p>
            <h3 className="h6">Hypothesis</h3>
            <p>{experiment.hypothesis}</p>
            {analysis.overall && <TableHighlights {...{ experiment }} />}
            <TableHighlightsOverview {...{ experiment }} />

            <div id="results_summary">
              <div className="d-flex justify-content-between mb-3">
                <h2 className="h5">Results Summary</h2>
                <button
                  data-testid="toggle-branch-comparison"
                  className="btn btn-secondary"
                  onClick={toggleBranchComparison}
                >
                  <small>See {toggleBranchComparisonText} comparison </small>
                </button>
              </div>
              {analysis.overall && (
                <TableResults {...{ experiment, branchComparison }} />
              )}

              {analysis.weekly && (
                <TableResultsWeekly
                  metricsList={HIGHLIGHTS_METRICS_LIST}
                  {...{ branchComparison }}
                />
              )}
            </div>

            <div>
              {analysis.overall &&
                experiment.primaryOutcomes?.map((slug) => {
                  const outcome = configOutcomes!.find((set) => {
                    return set?.slug === slug;
                  });
                  return outcome?.metrics?.map((metric) => (
                    <TableMetricCount
                      key={metric?.slug}
                      outcomeSlug={metric?.slug!}
                      outcomeDefaultName={metric?.friendlyName!}
                      group={GROUP.OTHER}
                      metricType={METRIC_TYPE.PRIMARY}
                    />
                  ));
                })}
              {analysis.overall &&
                experiment.secondaryOutcomes?.map((slug) => {
                  const outcome = configOutcomes!.find((set) => {
                    return set?.slug === slug;
                  });

                  return (
                    <TableMetricCount
                      key={outcome!.slug}
                      outcomeSlug={outcome!.slug!}
                      outcomeDefaultName={outcome!.friendlyName!}
                      group={GROUP.OTHER}
                      metricType={METRIC_TYPE.DEFAULT_SECONDARY}
                    />
                  );
                })}
              {analysis.other_metrics &&
                Object.keys(analysis.other_metrics).map((group: string) => {
                  const [open, setOpen] = groupStates[group];
                  const groupName = group.replace("_", " ");

                  return (
                    <div key={`${group}-toggle`}>
                      <span
                        onClick={() => {
                          setOpen(!open);
                        }}
                        aria-controls="group"
                        aria-expanded={open}
                        className="text-primary btn mb-5"
                      >
                        {open ? (
                          <>
                            <CollapseMinus />
                            <span style={{ textTransform: "capitalize" }}>
                              Hide {groupName}
                            </span>
                          </>
                        ) : (
                          <>
                            <ExpandPlus />
                            <span style={{ textTransform: "capitalize" }}>
                              Show {groupName}
                            </span>
                          </>
                        )}
                      </span>
                      <Collapse in={open}>
                        <div>
                          {analysis.other_metrics?.[group] &&
                            Object.keys(analysis.other_metrics[group]).map(
                              (metric: string) => (
                                <TableMetricCount
                                  key={metric}
                                  outcomeSlug={metric}
                                  outcomeDefaultName={
                                    analysis.other_metrics![group][metric]
                                  }
                                  {...{ group }}
                                />
                              ),
                            )}
                        </div>
                      </Collapse>
                    </div>
                  );
                })}
            </div>
          </ResultsContext.Provider>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageResults;
