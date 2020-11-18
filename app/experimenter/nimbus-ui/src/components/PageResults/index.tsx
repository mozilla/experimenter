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
import TableSummary from "../TableSummary";
import TableResults from "../TableResults";
import TableHighlights from "../TableHighlights";
import TableOverview from "../TableOverview";
import TableMetricPrimary from "../TableMetricPrimary";
import TableMetricSecondary from "../TableMetricSecondary";
import { AnalysisData } from "../../lib/visualization/types";

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
                {/* TODO: start/end dates with EXP-607 */}
                <LinkExternal
                  href={`https://grafana.telemetry.mozilla.org/d/XspgvdxZz/experiment-enrollment?orgId=1&var-experiment_id=${slug}`}
                  data-testid="link-monitoring-dashboard"
                >
                  Click here
                </LinkExternal>{" "}
                to view the live monitoring dashboard.
              </p>
              <h3 className="h5 my-3">Overview</h3>

              {error && <AnalysisFetchError />}
              {analysis?.show_analysis ? (
                <AnalysisAvailable {...{ experiment, analysis }} />
              ) : (
                <AnalysisUnavailable {...{ experiment }} />
              )}
            </>
          )}
        </>
      )}
    </AppLayoutWithExperiment>
  );
};

const AnalysisFetchError = () => (
  <Alert data-testid="analysis-error" variant="warning">
    Could not load experiment analysis data. Please contact data science in{" "}
    <LinkExternal href="https://mozilla.slack.com/archives/C0149JH7C1M">
      #cirrus
    </LinkExternal>{" "}
    about this.
  </Alert>
);

const AnalysisAvailable = ({
  experiment,
  analysis,
}: {
  experiment: getExperiment_experimentBySlug;
  analysis: AnalysisData | undefined;
}) => (
  <>
    <h3 className="h6">Hypothesis</h3>
    <p>{experiment.hypothesis}</p>
    <TableHighlights
      primaryProbeSets={experiment.primaryProbeSets!}
      results={analysis?.overall!}
    />
    <TableOverview />

    <h2 className="h5 my-3">Results</h2>
    <TableResults />
    <div>
      {experiment.primaryProbeSets?.map((probeSet) => (
        <TableMetricPrimary key={probeSet?.slug} />
      ))}
      {experiment.secondaryProbeSets?.map((probeSet) => (
        <TableMetricSecondary key={probeSet?.slug} />
      ))}
    </div>
  </>
);

const AnalysisUnavailable = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => {
  const slugUnderscored = experiment.slug.replace(/-/g, "_");
  return (
    <>
      <TableSummary {...{ experiment }} />
      <p>
        The results will be available 7 days after the experiment is launched.
        An email will be sent to you once we start recording data.
      </p>
      <p>
        The results{" "}
        <LinkExternal
          href={`https://protosaur.dev/partybal/${slugUnderscored}.html`}
          data-testid="link-external-results"
        >
          can be found here
        </LinkExternal>
        .
      </p>
    </>
  );
};

export default PageResults;
