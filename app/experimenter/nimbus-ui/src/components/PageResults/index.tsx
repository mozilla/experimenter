/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useContext, useState } from "react";
import Collapse from "react-bootstrap/Collapse";
import { useConfig } from "../../hooks";
import { ReactComponent as CollapseMinus } from "../../images/minus.svg";
import { ReactComponent as ExpandPlus } from "../../images/plus.svg";
import {
  ExperimentContext,
  ResultsContext,
  ResultsContextType,
} from "../../lib/contexts";
import { GROUP, METRIC_TYPE } from "../../lib/visualization/constants";
import {
  analysisUnavailable,
  getSortedBranchNames,
} from "../../lib/visualization/utils";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import ExternalConfigAlert from "./ExternalConfigAlert";
import TableHighlights from "./TableHighlights";
import TableHighlightsOverview from "./TableHighlightsOverview";
import TableMetricCount from "./TableMetricCount";
import TableResults from "./TableResults";
import TableResultsWeekly from "./TableResultsWeekly";
import TableWithTabComparison from "./TableWithTabComparison";

const PageResults: React.FunctionComponent<RouteComponentProps> = () => {
  const { experiment, analysis, useRedirectCondition, useAnalysisRequired } =
    useContext(ExperimentContext)!;

  useRedirectCondition(({ status, analysis }) => {
    if (!status?.launched) return "edit/overview";
    if (analysisUnavailable(analysis)) return "";
  });

  useAnalysisRequired();

  const { outcomes: configOutcomes } = useConfig();
  const groupStates: { [group: string]: any } = {
    usage_metrics: useState(true),
    search_metrics: useState(true),
    other_metrics: useState(true),
  };

  // For testing - users will be redirected if the analysis is unavailable
  // before reaching this return, but tests reach this return and
  // analysis.overall is expected to be an object (EXP-800)
  if (!analysis || analysisUnavailable(analysis)) return null;

  const sortedBranchNames = getSortedBranchNames(analysis);
  const resultsContextValue: ResultsContextType = {
    analysis,
    sortedBranchNames,
    controlBranchName: sortedBranchNames[0],
  };

  const { external_config: externalConfig } = analysis.metadata || {};

  return (
    <AppLayoutWithExperiment title="Analysis" testId="PageResults">
      <ResultsContext.Provider value={resultsContextValue}>
        {analysis?.metadata?.analysis_start_time && (
          <p>
            Results last calculated:{" "}
            <b>
              {new Date(analysis?.metadata?.analysis_start_time).toLocaleString(
                undefined,
                { timeZone: "UTC" },
              )}
            </b>
          </p>
        )}
        {externalConfig && <ExternalConfigAlert {...{ externalConfig }} />}

        <h3 className="h4 mb-3 mt-4" id="overview">
          Overview
        </h3>
        <p className="mb-4">
          <b>Hypothesis</b>: {experiment.hypothesis}
        </p>

        {analysis.overall && (
          <TableWithTabComparison
            {...{ experiment }}
            Table={TableHighlights}
            className="mb-2 border-top-0"
          />
        )}
        <TableHighlightsOverview {...{ experiment }} />

        <div id="results_summary">
          <h2 className="h4 mb-3">Results Summary</h2>
          {analysis.overall && (
            <TableWithTabComparison
              {...{ experiment }}
              Table={TableResults}
              className="rounded-bottom mb-3 border-top-0"
            />
          )}

          {analysis.weekly && (
            <TableWithTabComparison Table={TableResultsWeekly} />
          )}
        </div>

        <div>
          <h2 className="h4 mb-3">Outcome Metrics</h2>
          {analysis.overall &&
            experiment.primaryOutcomes?.map((slug) => {
              const outcome = configOutcomes!.find((set) => {
                return set?.slug === slug;
              });
              return outcome?.metrics?.map((metric) => {
                if (
                  !analysis!.overall![resultsContextValue.controlBranchName]
                    .branch_data[GROUP.OTHER][metric?.slug!]
                ) {
                  // Primary metric does not have data to display.
                  return;
                }
                return (
                  <TableMetricCount
                    key={metric?.slug}
                    outcomeSlug={metric?.slug!}
                    outcomeDefaultName={metric?.friendlyName!}
                    group={GROUP.OTHER}
                    metricType={METRIC_TYPE.PRIMARY}
                  />
                );
              });
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
                    onClick={
                      // istanbul ignore next - test covering this line intermittently fails
                      () => setOpen(!open)
                    }
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
    </AppLayoutWithExperiment>
  );
};

export default PageResults;
