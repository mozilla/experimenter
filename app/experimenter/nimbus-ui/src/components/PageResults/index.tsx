/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps, useParams } from "@reach/router";
import AppLayoutWithExperiment from "../AppLayoutWithExperiment";
import { useAnalysis } from "../../hooks";
import { Alert } from "react-bootstrap";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import LinkExternal from "../LinkExternal";
import TableResults from "../TableResults";
import TableHighlights from "../TableHighlights";
import TableHighlightsOverview from "../TableHighlightsOverview";
import TableMetricPrimary from "../TableMetricPrimary";
import TableMetricSecondary from "../TableMetricSecondary";
import { AnalysisData } from "../../lib/visualization/types";
import Summary from "../Summary";

const PageResults: React.FunctionComponent<RouteComponentProps> = () => {
  const { slug } = useParams();
  const { loading, error, result: analysis } = useAnalysis(slug);

  return (
    <AppLayoutWithExperiment title="Analysis" testId="PageResults">
      {({ experiment }) => (
        <>
          {loading ? (
            <p data-testid="analysis-loading">Loading analysis data...</p>
          ) : (
            <>
              <h3 className="h5 mb-3">Monitoring</h3>
              <p>
                <LinkExternal
                  href={experiment.monitoringDashboardUrl!}
                  data-testid="link-monitoring-dashboard"
                >
                  Click here
                </LinkExternal>{" "}
                to view the live monitoring dashboard.
              </p>
              {analysis?.show_analysis ? (
                <AnalysisAvailable {...{ experiment, analysis }} />
              ) : (
                <AnalysisUnavailable {...{ experiment, error }} />
              )}
            </>
          )}
        </>
      )}
    </AppLayoutWithExperiment>
  );
};

const AnalysisAvailable = ({
  experiment,
  analysis,
}: {
  experiment: getExperiment_experimentBySlug;
  analysis: AnalysisData | undefined;
}) => {
  const slugUnderscored = experiment.slug.replace(/-/g, "_");
  return (
    <>
      <h3 className="h5 mb-3 mt-4">Overview</h3>
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

      <h2 className="h5 mb-3">Results</h2>
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
            key={probeSet?.slug}
            results={analysis?.overall!}
            probeSet={probeSet!}
          />
        ))}
      </div>
    </>
  );
};

const AlertError = () => (
  <Alert data-testid="analysis-error" variant="warning" className="my-4">
    Could not load experiment analysis data. Please contact data science in{" "}
    <LinkExternal href="https://mozilla.slack.com/archives/C0149JH7C1M">
      #cirrus
    </LinkExternal>{" "}
    about this.
  </Alert>
);

const AlertUnavailable = () => (
  <Alert data-testid="analysis-unavailable" variant="warning" className="my-4">
    <p>
      <strong>The analysis is not yet available.</strong>
    </p>
    <p className="mb-0">
      {" "}
      The results will be available 7 days after the experiment is launched. An
      email will be sent to you once we start recording data.
    </p>
  </Alert>
);

const AnalysisUnavailable = ({
  experiment,
  error,
}: {
  experiment: getExperiment_experimentBySlug;
  error: Error | undefined;
}) => (
  <>
    {error ? <AlertError /> : <AlertUnavailable />}
    <Summary {...{ experiment }} />
  </>
);

export default PageResults;
