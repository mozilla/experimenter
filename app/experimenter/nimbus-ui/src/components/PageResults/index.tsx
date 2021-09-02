/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useState } from "react";
import Collapse from "react-bootstrap/Collapse";
import { useConfig } from "../../hooks";
import { ReactComponent as ExternalIcon } from "../../images/external.svg";
import { ReactComponent as CollapseMinus } from "../../images/minus.svg";
import { ReactComponent as ExpandPlus } from "../../images/plus.svg";
import { ResultsContext, ResultsContextType } from "../../lib/contexts";
import { GROUP, METRIC_TYPE } from "../../lib/visualization/constants";
import {
  analysisUnavailable,
  getSortedBranchNames,
} from "../../lib/visualization/utils";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import LinkExternal from "../LinkExternal";
import ExternalConfigAlert from "./ExternalConfigAlert";
import TableHighlights from "./TableHighlights";
import TableHighlightsOverview from "./TableHighlightsOverview";
import TableMetricCount from "./TableMetricCount";
import TableResults from "./TableResults";
import TableResultsWeekly from "./TableResultsWeekly";
import TableWithTabComparison from "./TableWithTabComparison";

const PageResults: React.FunctionComponent<RouteComponentProps> = () => {
  const { outcomes: configOutcomes } = useConfig();
  const groupStates: { [group: string]: any } = {
    usage_metrics: useState(true),
    search_metrics: useState(true),
    other_metrics: useState(true),
  };

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

        const sortedBranchNames = getSortedBranchNames(analysis);
        const resultsContextValue: ResultsContextType = {
          analysis,
          sortedBranchNames,
          controlBranchName: sortedBranchNames[0],
        };

        const { external_config: externalConfig } = analysis.metadata || {};
        const slugUnderscored = experiment.slug.replace(/-/g, "_");

        return (
          <ResultsContext.Provider value={resultsContextValue}>
            {externalConfig && <ExternalConfigAlert {...{ externalConfig }} />}

            <p className="mb-1">
              <LinkExternal
                href={experiment.monitoringDashboardUrl!}
                data-testid="link-monitoring-dashboard"
              >
                Live Monitoring Dashboard <ExternalIcon />
              </LinkExternal>
            </p>
            <p>
              <LinkExternal
                href={`https://protosaur.dev/partybal/${slugUnderscored}.html`}
                data-testid="link-external-results"
              >
                Detailed Analysis <ExternalIcon />
              </LinkExternal>
            </p>
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
