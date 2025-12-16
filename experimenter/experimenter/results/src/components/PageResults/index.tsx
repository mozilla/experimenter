/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useContext, useState } from "react";
import { Alert, Card, Form } from "react-bootstrap";
import Col from "react-bootstrap/Col";
import Collapse from "react-bootstrap/Collapse";
import Nav from "react-bootstrap/Nav";
import Row from "react-bootstrap/Row";
import LinkExternal from "src/components/LinkExternal";
import AnalysisErrorAlert from "src/components/PageResults/AnalysisErrorAlert";
import ExternalConfigAlert from "src/components/PageResults/ExternalConfigAlert";
import TableHighlights from "src/components/PageResults/TableHighlights";
import TableHighlightsOverview from "src/components/PageResults/TableHighlightsOverview";
import TableMetricCount from "src/components/PageResults/TableMetricCount";
import MetricHeader from "src/components/PageResults/TableMetricCount/MetricHeader";
import TableResults from "src/components/PageResults/TableResults";
import TableResultsWeekly from "src/components/PageResults/TableResultsWeekly";
import TableWithTabComparison from "src/components/PageResults/TableWithTabComparison";
import TooltipWithMarkdown from "src/components/PageResults/TooltipWithMarkdown";
import { useConfig, useOutcomes } from "src/hooks";
import { ReactComponent as Info } from "src/images/info.svg";
import { ReactComponent as CollapseMinus } from "src/images/minus.svg";
import { ReactComponent as ExpandPlus } from "src/images/plus.svg";
import {
  ExperimentContext,
  ResultsContext,
  ResultsContextType,
} from "src/lib/contexts";
import { OutcomesList } from "src/lib/types";
import { GROUP, METRIC_TYPE } from "src/lib/visualization/constants";
import {
  AnalysisBases,
  AnalysisError,
  MetadataPoint,
} from "src/lib/visualization/types";
import { getSortedBranchNames } from "src/lib/visualization/utils";

const outcomeToMapping = (outcomes: OutcomesList) => {
  const response = outcomes.reduce(
    (acc: { [key: string]: string }, outcome) => {
      outcome?.metrics?.forEach((metric) => {
        acc[metric?.slug as string] = metric?.friendlyName!;
      });

      return acc;
    },
    {},
  );
  return response;
};

const otherMetricsToFriendlyName = (
  otherMetrics: { [group: string]: { [metric: string]: string } },
  metricsMetaData: { [metric: string]: MetadataPoint },
) => {
  const newMap: { [key: string]: string } = {};
  Object.keys(otherMetrics).forEach((group) => {
    Object.keys(otherMetrics[group]).forEach((metric) => {
      /* istanbul ignore next */
      newMap[metric] =
        metricsMetaData[metric]?.friendly_name || otherMetrics[group][metric]; //
    });
  });
  return newMap;
};

const PageResults: React.FunctionComponent<RouteComponentProps> = () => {
  const { experiment, analysis, useRedirectCondition, useAnalysisRequired } =
    useContext(ExperimentContext)!;

  const { primaryOutcomes, secondaryOutcomes } = useOutcomes(experiment);
  const primaryMetrics = outcomeToMapping(primaryOutcomes);
  const secondaryMetrics = outcomeToMapping(secondaryOutcomes);

  const otherMetrics = otherMetricsToFriendlyName(
    analysis?.other_metrics || {},
    analysis?.metadata?.metrics || {},
  );

  const getNestedSidebarItems = (
    metrics: { [metric: string]: string },
    title: string,
  ) => {
    const sidebarItems = Object.keys(metrics).map((sidebarKey) => {
      /* istanbul ignore next */
      const metricName = metrics[sidebarKey] || sidebarKey;
      return (
        <li className="font-weight-normal ml-4 mb-2" key={metricName}>
          <a
            href={`#${sidebarKey}`}
            className="inherit-color font-weight-normal"
          >
            {metricName}
          </a>
        </li>
      );
    });

    sidebarItems.unshift(
      <li key={title} className="mb-2 ml-3">
        {title}
      </li>,
    );
    return sidebarItems;
  };

  const ResultsAvailableNav = () => (
    <>
      <li>
        <ul className="list-unstyled">
          {Object.keys(primaryMetrics).length > 0 &&
            getNestedSidebarItems(primaryMetrics, "Primary Outcomes")}
          {Object.keys(secondaryMetrics).length > 0 &&
            getNestedSidebarItems(secondaryMetrics, "Secondary Outcomes")}
          {otherMetrics &&
            analysis?.overall &&
            getNestedSidebarItems(otherMetrics, "Default Metrics")}
        </ul>
      </li>
    </>
  );

  useRedirectCondition(({ status, experiment, analysis }) => {
    if (!status?.launched) return "edit/overview";
    // explicitly check for false to avoid undefined being falsy
    if (
      experiment?.showResultsUrl === false ||
      analysis?.show_analysis === false
    )
      return "";
  });

  useAnalysisRequired();

  const { outcomes: configOutcomes } = useConfig();
  const groupStates: { [group: string]: any } = {
    usage_metrics: useState(true),
    search_metrics: useState(true),
    other_metrics: useState(true),
  };

  const [selectedSegment, setSelectedSegment] = useState<string>("all");

  const [selectedAnalysisBasis, setSelectedAnalysisBasis] =
    useState<AnalysisBases>("exposures");

  const [selectedReferenceBranch, setSelectedReferenceBranch] =
    useState<string>("");

  // For testing - users will be redirected if the analysis is unavailable
  // before reaching this return, but tests reach this return and
  // analysis.overall is expected to be an object (EXP-800)
  if (
    !analysis ||
    experiment?.showResultsUrl === false ||
    analysis?.show_analysis === false
  )
    return null;

  const sortedBranchNames = getSortedBranchNames(analysis, experiment);
  const controlBranchSlug =
    sortedBranchNames.length > 0
      ? sortedBranchNames[0]
      : experiment.referenceBranch?.slug;
  if (selectedReferenceBranch === "" && controlBranchSlug) {
    setSelectedReferenceBranch(controlBranchSlug);
  }
  const resultsContextValue: ResultsContextType = {
    analysis,
    sortedBranchNames,
    controlBranchName: controlBranchSlug || "",
  };

  // list of metrics (slugs) with errors that would not otherwise be displayed
  const otherMetricErrors = Object.keys(analysis?.errors || {}).filter(
    (key: string) => {
      if (key === "experiment") {
        return false;
      }
      if (
        configOutcomes &&
        configOutcomes.find(
          (outcome) =>
            outcome?.slug === key &&
            outcome?.application === experiment.application,
        )
      ) {
        return false;
      }

      const errorsForState = analysis.errors![key].filter(
        (error) =>
          (error.analysis_basis === selectedAnalysisBasis ||
            error.analysis_basis === null) &&
          (error.segment === selectedSegment || error.segment === null),
      );

      return errorsForState.length > 0;
    },
  );

  const controlBranchError =
    sortedBranchNames.length === 0 ? (
      <AnalysisErrorAlert
        errors={[
          {
            metric: null,
            message:
              "No control branch found in analysis results. Usually this error indicates that results are not available yet.",
            filename: null,
            exception: null,
            func_name: null,
            log_level: null,
            statistic: null,
            timestamp: null,
            experiment: null,
            exception_type: null,
            analysis_basis: null,
            segment: null,
          },
        ]}
      />
    ) : null;

  const { external_config: externalConfig } = analysis.metadata || {};

  const referenceBranchHelpMarkdown =
    "Select the **reference branch** to set it as the baseline for comparison results. By default this is the experiment's configured reference branch (commonly named 'control').";

  const allAnalysisBases: AnalysisBases[] =
    Object.keys(analysis?.overall || {}).length > 0
      ? (Object.keys(analysis?.overall || {}).sort() as AnalysisBases[])
      : (Object.keys(analysis?.weekly || {}).sort() as AnalysisBases[]);
  const analysisBasisHelpMarkdown =
    "Select the **analysis basis** whose results you want to see. See [defining exposure signals](https://experimenter.info/jetstream/configuration/#defining-exposure-signals) in the docs for more info.";

  const allSegments = Object.keys(analysis?.overall?.enrollments || {}).sort();
  const segmentHelpMarkdown =
    "Select the **analysis segment** whose results you want to see. See [defining segments](https://experimenter.info/jetstream/configuration/#defining-segments) in the docs for more info.";

  const filterErrors = (
    errors: AnalysisError[],
    analysisBasis: AnalysisBases,
    segment: string,
  ): AnalysisError[] =>
    errors.filter(
      // filter to selected analysis_basis + segment and de-dupe with findIndex
      (error, idx, self) =>
        (error.analysis_basis === analysisBasis ||
          error.analysis_basis === null) &&
        (error.segment === segment || error.segment === null) &&
        idx ===
          self.findIndex(
            (e) =>
              e.message === error.message &&
              e.segment === error.segment &&
              e.analysis_basis === error.analysis_basis,
          ),
    );

  const getErrorsForOutcomes = (
    outcomes: (string | null)[] | null,
    isPrimary: boolean,
  ): React.ReactElement => {
    return (
      <>
        {outcomes?.map((slug) => {
          const outcome = configOutcomes!.find((set) => {
            return (
              set?.slug === slug && set?.application === experiment.application
            );
          });
          return outcome?.metrics?.map((metric) => {
            if (metric?.slug) {
              // if we have more than just the 'experiment' errors key,
              // that means at least one metric had errors, so we should
              // show all the metric headers to avoid potential confusion
              const metricHeader = (
                <MetricHeader
                  key={metric.slug}
                  outcomeSlug={metric.slug!}
                  outcomeDefaultName={metric?.friendlyName!}
                  metricType={
                    isPrimary
                      ? METRIC_TYPE.PRIMARY
                      : METRIC_TYPE.DEFAULT_SECONDARY
                  }
                />
              );
              if (
                metric.slug in analysis.errors! &&
                analysis.errors![metric.slug].length > 0
              ) {
                return (
                  <>
                    {metricHeader}
                    <AnalysisErrorAlert
                      errors={filterErrors(
                        analysis.errors![metric.slug],
                        selectedAnalysisBasis,
                        selectedSegment,
                      )}
                    />
                  </>
                );
              } else {
                return (
                  <>
                    {metricHeader}
                    <p>
                      <i>No results available for metric.</i>
                    </p>
                  </>
                );
              }
            }
          });
        })}
      </>
    );
  };

  const exposureEventsInfoUrl = "https://experimenter.info/missing-exposure";

  return (
    <ResultsContext.Provider value={resultsContextValue}>
      <Row data-testid="PageResults">
        <Col sm="2" className="p-0">
          <Card>
            <Card.Header as="h5" style={{ paddingLeft: "0.5rem" }}>
              Results Config
            </Card.Header>
            <Card.Body
              className="border-left-0 border-right-0 border-bottom-0"
              style={{ padding: "0.5rem" }}
            >
              {allAnalysisBases.length > 1 && (
                <>
                  <div>
                    <b>Analysis Basis</b>:
                    <span className="align-middle">
                      <Info
                        className="align-baseline"
                        data-tip
                        data-for="analysis-basis-help"
                      />
                    </span>
                    <TooltipWithMarkdown
                      tooltipId="analysis-basis-help"
                      markdown={analysisBasisHelpMarkdown}
                    />
                  </div>
                  <div data-testid="analysis-basis-results-selector">
                    {allAnalysisBases.map((basis) => (
                      <div
                        style={{ marginTop: "0.25rem", marginLeft: "0.5rem" }}
                        key={`${basis}_basis_radio_option`}
                      >
                        <Form.Check
                          inline
                          radioGroup="analysis-basis-group"
                          type="radio"
                          onChange={() => setSelectedAnalysisBasis(basis)}
                          label={basis}
                          checked={basis === selectedAnalysisBasis}
                          data-testid={`${basis}-basis-radio`}
                        />
                      </div>
                    ))}
                  </div>
                </>
              )}
              {sortedBranchNames.length > 1 && (
                <>
                  <div style={{ marginTop: "1rem" }}>
                    <b>Reference Branch</b>:
                    <span className="align-middle">
                      <Info
                        className="align-baseline"
                        data-tip
                        data-for="reference-branch-help"
                      />
                    </span>
                    <TooltipWithMarkdown
                      tooltipId="reference-branch-help"
                      markdown={referenceBranchHelpMarkdown}
                    />
                  </div>
                  <div data-testid="reference-branch-results-selector">
                    {sortedBranchNames.map((branch) => (
                      <div
                        style={{ marginTop: "0.25rem", marginLeft: "0.5rem" }}
                        key={`${branch}_branch_radio_option`}
                      >
                        <Form.Check
                          inline
                          radioGroup="reference-branch-group"
                          type="radio"
                          onChange={() => setSelectedReferenceBranch(branch)}
                          label={branch}
                          checked={branch === selectedReferenceBranch}
                          data-testid={`${branch}-branch-radio`}
                        />
                      </div>
                    ))}
                  </div>
                </>
              )}
              {allSegments.length > 1 && (
                <>
                  <div style={{ marginTop: "1rem" }}>
                    <b>Segment</b>:
                    <span className="align-middle">
                      <Info
                        className="align-baseline"
                        data-tip
                        data-for="segments-help"
                      />
                    </span>
                    <TooltipWithMarkdown
                      tooltipId="segments-help"
                      markdown={segmentHelpMarkdown}
                    />
                  </div>
                  <div data-testid="segment-results-selector">
                    {allSegments.map((segment) => (
                      <div
                        style={{ marginTop: "0.25rem", marginLeft: "0.5rem" }}
                        key={`${segment}_segment_radio_option`}
                      >
                        <Form.Check
                          inline
                          radioGroup="segment-radio-group"
                          type="radio"
                          onChange={() => setSelectedSegment(segment)}
                          label={segment.replace(/_/g, " ")}
                          checked={segment === selectedSegment}
                          data-testid={`${segment}-segment-radio`}
                        />
                      </div>
                    ))}
                  </div>
                </>
              )}
              {analysis?.metadata?.analysis_start_time && (
                <div style={{ marginTop: "1.5rem" }}>
                  Results last calculated:{" "}
                  <b>
                    {new Date(
                      analysis?.metadata?.analysis_start_time,
                    ).toLocaleString(undefined, {
                      timeZone: "UTC",
                      timeZoneName: "short",
                    })}
                  </b>
                </div>
              )}
            </Card.Body>
          </Card>
          <Nav className="font-weight-semibold mt-2" as="ul">
            <ResultsAvailableNav />
          </Nav>
        </Col>
        <Col>
          <Alert variant="warning" data-testid="exposures-as-default-alert">
            <Alert.Heading>
              Analysis Results now default to Exposures basis
            </Alert.Heading>
            <p>
              The results shown on this page now default to the Exposures
              analysis basis. This does not change the available results (i.e.,
              results for Enrollments are still available), and you can still
              select any available Analysis Basis via the radio buttons on the
              left.
            </p>
            <ul className="pl-0">
              <strong>Results not available or not what you expected?</strong>{" "}
              <LinkExternal
                href={exposureEventsInfoUrl}
                data-testid="external-config-url"
              >
                Click here
              </LinkExternal>{" "}
              for more information about Exposure events, including how to set
              up experiments that have exposure events analysis results.
            </ul>
            <p>
              If you have questions about this, please ask data science in{" "}
              <LinkExternal href="https://mozilla.slack.com/archives/CF94YGE03">
                #ask-experimenter
              </LinkExternal>
              .
            </p>
          </Alert>

          {analysis?.errors?.experiment &&
            analysis?.errors?.experiment.length > 0 && (
              <AnalysisErrorAlert errors={analysis.errors.experiment} />
            )}

          {externalConfig && <ExternalConfigAlert {...{ externalConfig }} />}

          <p className="mb-4">
            <b>Hypothesis</b>: {experiment.hypothesis}
          </p>

          {analysis.overall?.[selectedAnalysisBasis]?.[selectedSegment] &&
            Object.keys(
              analysis.overall?.[selectedAnalysisBasis]?.[selectedSegment] ||
                {},
            ).length > 0 && (
              <TableWithTabComparison
                {...{ experiment }}
                Table={TableHighlights}
                className="mb-2 border-top-0"
                analysisBasis={selectedAnalysisBasis}
                segment={selectedSegment}
                referenceBranch={selectedReferenceBranch}
              />
            )}
          <TableHighlightsOverview {...{ experiment }} />

          <div id="results_summary">
            <h2 className="h4 mb-3">Results Summary</h2>
            {analysis.overall?.[selectedAnalysisBasis]?.[selectedSegment] &&
              Object.keys(
                analysis.overall?.[selectedAnalysisBasis]?.[selectedSegment] ||
                  {},
              ).length > 0 && (
                <TableWithTabComparison
                  {...{ experiment }}
                  Table={TableResults}
                  className="rounded-bottom mb-3 border-top-0"
                  analysisBasis={selectedAnalysisBasis}
                  segment={selectedSegment}
                  referenceBranch={selectedReferenceBranch}
                />
              )}

            {analysis.weekly?.[selectedAnalysisBasis]?.[selectedSegment] &&
              Object.keys(
                analysis.weekly?.[selectedAnalysisBasis]?.[selectedSegment] ||
                  {},
              ).length > 0 && (
                <TableWithTabComparison
                  Table={TableResultsWeekly}
                  analysisBasis={selectedAnalysisBasis}
                  segment={selectedSegment}
                  referenceBranch={selectedReferenceBranch}
                />
              )}
          </div>

          <div>
            <h2 className="h4 mb-3">Outcome Metrics</h2>
            {controlBranchError}
            {analysis.overall?.[selectedAnalysisBasis]?.[selectedSegment] &&
            Object.keys(
              analysis.overall?.[selectedAnalysisBasis]?.[selectedSegment] ||
                {},
            ).length > 0
              ? experiment.primaryOutcomes?.map((slug) => {
                  const outcome = configOutcomes!.find((set) => {
                    return (
                      set?.slug === slug &&
                      set?.application === experiment.application
                    );
                  });
                  return outcome?.metrics?.map((metric) => {
                    if (
                      !analysis!.overall![selectedAnalysisBasis]?.[
                        selectedSegment
                      ]?.[selectedReferenceBranch]?.branch_data[GROUP.OTHER][
                        metric?.slug!
                      ]
                    ) {
                      // Primary metric does not have data to display. Show error if there is one.
                      if (
                        metric?.slug &&
                        analysis?.errors &&
                        metric.slug in analysis.errors &&
                        analysis.errors[metric.slug].length > 0
                      ) {
                        return (
                          <>
                            <MetricHeader
                              key={metric.slug}
                              outcomeSlug={metric.slug!}
                              outcomeDefaultName={metric?.friendlyName!}
                              metricType={METRIC_TYPE.PRIMARY}
                            />
                            <AnalysisErrorAlert
                              errors={analysis.errors[metric.slug]}
                            />
                          </>
                        );
                      }
                    }
                    return (
                      <TableMetricCount
                        key={metric?.slug}
                        outcomeSlug={metric?.slug!}
                        outcomeDefaultName={metric?.friendlyName!}
                        group={GROUP.OTHER}
                        metricType={METRIC_TYPE.PRIMARY}
                        analysisBasis={selectedAnalysisBasis}
                        segment={selectedSegment}
                        referenceBranch={selectedReferenceBranch}
                      />
                    );
                  });
                })
              : // no Overall results, check for errors in primary outcome metrics
                analysis?.errors &&
                Object.keys(analysis.errors).length > 1 &&
                getErrorsForOutcomes(experiment.primaryOutcomes, true)}
            {analysis.overall?.[selectedAnalysisBasis]?.[selectedSegment] &&
            Object.keys(
              analysis.overall?.[selectedAnalysisBasis]?.[selectedSegment] ||
                {},
            ).length > 0
              ? experiment.secondaryOutcomes?.map((slug) => {
                  const outcome = configOutcomes!.find((set) => {
                    return (
                      set?.slug === slug &&
                      set?.application === experiment.application
                    );
                  });
                  return outcome?.metrics?.map((metric) => {
                    if (
                      !analysis!.overall![selectedAnalysisBasis]?.[
                        selectedSegment
                      ]?.[selectedReferenceBranch]?.branch_data[GROUP.OTHER][
                        metric?.slug!
                      ]
                    ) {
                      // Secondary metric does not have data to display. Show error if there is one.
                      if (
                        metric?.slug &&
                        analysis?.errors &&
                        metric.slug in analysis.errors &&
                        analysis.errors[metric.slug].length > 0
                      ) {
                        return (
                          <>
                            <MetricHeader
                              key={metric.slug}
                              outcomeSlug={metric.slug!}
                              outcomeDefaultName={metric?.friendlyName!}
                              metricType={METRIC_TYPE.USER_SELECTED_SECONDARY}
                            />
                            <AnalysisErrorAlert
                              errors={analysis.errors[metric.slug]}
                            />
                          </>
                        );
                      }
                    }
                    return (
                      <TableMetricCount
                        key={metric?.slug}
                        outcomeSlug={metric?.slug!}
                        outcomeDefaultName={metric?.friendlyName!}
                        group={GROUP.OTHER}
                        metricType={METRIC_TYPE.USER_SELECTED_SECONDARY}
                        analysisBasis={selectedAnalysisBasis}
                        segment={selectedSegment}
                        referenceBranch={selectedReferenceBranch}
                      />
                    );
                  });
                })
              : // no Overall results, check for errors in secondary outcome metrics
                analysis?.errors &&
                Object.keys(analysis.errors).length > 1 &&
                getErrorsForOutcomes(experiment.secondaryOutcomes, false)}
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
                        {analysis.overall?.[selectedAnalysisBasis]?.[
                          selectedSegment
                        ] &&
                          Object.keys(
                            analysis.overall?.[selectedAnalysisBasis]?.[
                              selectedSegment
                            ] || {},
                          ).length > 0 &&
                          analysis.other_metrics?.[group] &&
                          Object.keys(analysis.other_metrics[group]).map(
                            (metric: string) => (
                              <TableMetricCount
                                key={metric}
                                outcomeSlug={metric}
                                outcomeDefaultName={
                                  analysis.other_metrics![group][metric]
                                }
                                {...{ group }}
                                analysisBasis={selectedAnalysisBasis}
                                segment={selectedSegment}
                                referenceBranch={selectedReferenceBranch}
                              />
                            ),
                          )}
                      </div>
                    </Collapse>
                  </div>
                );
              })}
            {otherMetricErrors.length > 0 && (
              <>
                <h3 className="h5 mb-3">
                  <i>Other Metric Errors</i>
                </h3>
                {otherMetricErrors.map((errorMetric) => (
                  <>
                    <MetricHeader
                      key={errorMetric}
                      outcomeSlug={errorMetric}
                      outcomeDefaultName={errorMetric}
                      metricType={METRIC_TYPE.USER_SELECTED_SECONDARY}
                    />
                    <AnalysisErrorAlert
                      errors={filterErrors(
                        analysis.errors?.[errorMetric] || [],
                        selectedAnalysisBasis,
                        selectedSegment,
                      )}
                    />
                  </>
                ))}
              </>
            )}
          </div>
        </Col>
      </Row>
    </ResultsContext.Provider>
  );
};

export default PageResults;
