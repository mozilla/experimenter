/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useContext } from "react";
import { AnalysisContext, ExperimentContext } from "../../lib/contexts";
import { analysisUnavailable } from "../../lib/visualization/utils";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import LinkExternal from "../LinkExternal";
import LinkMonitoring from "../LinkMonitoring";
import TableHighlights from "./TableHighlights";
import TableHighlightsOverview from "./TableHighlightsOverview";
import TableMetricPrimary from "./TableMetricPrimary";
import TableMetricSecondary from "./TableMetricSecondary";
import TableResults from "./TableResults";

const PageResults: React.FunctionComponent<RouteComponentProps> = () => {
  const { experiment } = useContext(ExperimentContext);
  const { analysis } = useContext(AnalysisContext);
  const {
    slug,
    hypothesis,
    primaryProbeSets,
    secondaryProbeSets,
    monitoringDashboardUrl,
  } = experiment!;

  const slugUnderscored = slug.replace(/-/g, "_");

  // For testing - users will be redirected if the analysis is unavailable
  // before reaching this return, but tests reach this return and
  // analysis.overall is expected to be an object (EXP-800)
  if (analysisUnavailable(analysis)) return <></>;

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
          return "design";
        }
      }}
    >
      <LinkMonitoring {...{ monitoringDashboardUrl }} />
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
      <p>{hypothesis}</p>
      <TableHighlights />
      <TableHighlightsOverview />
      <h2 className="h5 mb-3" id="results-summary">
        Results Summary
      </h2>
      <TableResults />
      <div>
        {primaryProbeSets?.map((probeSet) => (
          <TableMetricPrimary key={probeSet?.slug} probeSet={probeSet!} />
        ))}
        {analysis &&
          secondaryProbeSets?.map((probeSet) => (
            <TableMetricSecondary
              key={probeSet!.slug}
              probeSetSlug={probeSet!.slug}
              probeSetName={probeSet!.name}
              isDefault={false}
            />
          ))}
        {analysis?.other_metrics &&
          Object.keys(analysis.other_metrics).map((metric) => (
            <TableMetricSecondary
              key={metric}
              probeSetSlug={metric}
              probeSetName={analysis!.other_metrics![metric]}
            />
          ))}
      </div>
    </AppLayoutWithExperiment>
  );
};

export default PageResults;
