/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React from "react";
import { useConfig } from "../../hooks";
import { HIGHLIGHTS_METRICS_LIST } from "../../lib/visualization/constants";
import { analysisUnavailable } from "../../lib/visualization/utils";
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

  return (
    <AppLayoutWithExperiment
      title="Analysis"
      testId="PageResults"
      analysisRequired
      redirect={({ status, analysis }) => {
        if (!status?.released) {
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
              <TableHighlights results={analysis!} {...{ experiment }} />
            )}
            <TableHighlightsOverview
              {...{ experiment }}
              results={analysis?.overall!}
            />

            <div id="results-summary">
              <h2 className="h5 mb-3">Results Summary</h2>
              {analysis?.overall && (
                <TableResults {...{ experiment }} results={analysis!} />
              )}

              {analysis?.weekly && (
                <TableResultsWeekly
                  weeklyResults={analysis.weekly}
                  hasOverallResults={!!analysis?.overall}
                  metricsList={HIGHLIGHTS_METRICS_LIST}
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
                      isDefault={false}
                    />
                  );
                })}
              {analysis?.other_metrics &&
                Object.keys(analysis.other_metrics).map((metric: string) => (
                  <TableMetricSecondary
                    key={metric}
                    results={analysis}
                    outcomeSlug={metric}
                    outcomeDefaultName={analysis!.other_metrics![metric]}
                  />
                ))}
            </div>
          </>
        );
      }}
    </AppLayoutWithExperiment>
  );
};

export default PageResults;
