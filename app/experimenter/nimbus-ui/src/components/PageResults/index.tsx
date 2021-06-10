/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useState } from "react";
import Collapse from "react-bootstrap/Collapse";
import { useConfig } from "../../hooks";
import { ReactComponent as CollapseMinus } from "../../images/minus.svg";
import { ReactComponent as ExpandPlus } from "../../images/plus.svg";
import {
  GROUP,
  HIGHLIGHTS_METRICS_LIST,
} from "../../lib/visualization/constants";
import {
  analysisUnavailable,
  getSortedBranches,
} from "../../lib/visualization/utils";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import LinkExternal from "../LinkExternal";
import LinkMonitoring from "../LinkMonitoring";
import TableHighlights from "./TableHighlights";
import TableHighlightsOverview from "./TableHighlightsOverview";
import TableMetricPrimary from "./TableMetricPrimary";
import TableMetricSecondary from "./TableMetricSecondary";
import TableResults from "./TableResults";
import TableResultsWeekly from "./TableResultsWeekly";

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
        if (analysisUnavailable(analysis)) return;

        const slugUnderscored = experiment.slug.replace(/-/g, "_");
        const sortedBranches = getSortedBranches(analysis!);
        return (
          <>
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
            {analysis?.overall && (
              <TableHighlights
                results={analysis}
                {...{ experiment, sortedBranches }}
              />
            )}
            <TableHighlightsOverview {...{ experiment }} />

            <div id="results_summary">
              <h2 className="h5 mb-3">Results Summary</h2>
              {analysis?.overall && (
                <TableResults
                  {...{ experiment, sortedBranches }}
                  results={analysis!}
                />
              )}

              {analysis?.weekly && (
                <TableResultsWeekly
                  weeklyResults={analysis.weekly}
                  hasOverallResults={!!analysis?.overall}
                  metricsList={HIGHLIGHTS_METRICS_LIST}
                  {...{ sortedBranches }}
                />
              )}
            </div>

            <div>
              {experiment.primaryOutcomes?.map((slug) => {
                const outcome = configOutcomes!.find((set) => {
                  return set?.slug === slug;
                });

                return (
                  <TableMetricPrimary
                    key={slug}
                    results={analysis?.overall!}
                    outcome={outcome!}
                    {...{ sortedBranches }}
                  />
                );
              })}
              {analysis &&
                experiment.secondaryOutcomes?.map((slug) => {
                  const outcome = configOutcomes!.find((set) => {
                    return set?.slug === slug;
                  });

                  return (
                    <TableMetricSecondary
                      key={outcome!.slug}
                      results={analysis}
                      outcomeSlug={outcome!.slug!}
                      outcomeDefaultName={outcome!.friendlyName!}
                      group={GROUP.OTHER}
                      isDefault={false}
                      {...{ sortedBranches }}
                    />
                  );
                })}
              {analysis?.other_metrics &&
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
                                <TableMetricSecondary
                                  key={metric}
                                  results={analysis}
                                  outcomeSlug={metric}
                                  outcomeDefaultName={
                                    analysis!.other_metrics![group][metric]
                                  }
                                  group={group}
                                  {...{ sortedBranches }}
                                />
                              ),
                            )}
                        </div>
                      </Collapse>
                    </div>
                  );
                })}
            </div>
          </>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageResults;
