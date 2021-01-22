/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import LinkExternal from "../LinkExternal";
import TableResults from "./TableResults";
import TableHighlights from "./TableHighlights";
import TableHighlightsOverview from "./TableHighlightsOverview";
import TableMetricPrimary from "./TableMetricPrimary";
import TableMetricSecondary from "./TableMetricSecondary";
import LinkMonitoring from "../LinkMonitoring";
import { analysisUnavailable } from "../../lib/visualization/utils";

const PageResults: React.FunctionComponent<RouteComponentProps> = () => (
  <AppLayoutWithExperiment
    title="Analysis"
    testId="PageResults"
    analysisRequired
    redirect={({ status, analysis }) => {
      if (!status?.released) {
        return "edit/overview";
      }

      if (analysisUnavailable(analysis)) {
        return "design";
      }
    }}
  >
    {({ experiment, analysis }) => {
      // For testing - users will be redirected if the analysis is unavailable
      // before reaching this return, but tests reach this return and
      // analysis.overall is expected to be an object (EXP-800)
      if (analysisUnavailable(analysis)) return <></>;

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
          <TableHighlights
            primaryProbeSets={experiment.primaryProbeSets!}
            results={analysis?.overall!}
          />
          <TableHighlightsOverview
            {...{ experiment }}
            results={analysis?.overall!}
          />

          <h2 className="h5 mb-3" id="results-summary">
            Results Summary
          </h2>
          <TableResults
            primaryProbeSets={experiment.primaryProbeSets!}
            results={analysis?.overall!}
          />
          <div>
            {experiment.primaryProbeSets?.map((probeSet) => (
              <TableMetricPrimary
                key={probeSet?.slug}
                results={analysis?.overall!}
                probeSet={probeSet!}
              />
            ))}
            {experiment.secondaryProbeSets?.map((probeSet) => (
              <TableMetricSecondary
                key={probeSet!.slug}
                results={analysis?.overall!}
                probeSetSlug={probeSet!.slug}
                probeSetName={probeSet!.name}
                isDefault={false}
              />
            ))}
            {analysis?.other_metrics &&
              Object.keys(analysis.other_metrics).map((metric) => (
                <TableMetricSecondary
                  key={metric}
                  results={analysis?.overall!}
                  probeSetSlug={metric}
                  probeSetName={analysis!.other_metrics![metric]}
                />
              ))}
          </div>
        </>
      );
    }}
  </AppLayoutWithExperiment>
);

export default PageResults;
