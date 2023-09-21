/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps, useParams } from "@reach/router";
import React from "react";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Row from "react-bootstrap/Row";
import { ReactComponent as BarChart } from "src/components/AppLayoutSidebarLaunched/bar-chart.svg";
import { ReactComponent as Person } from "src/components/AppLayoutWithSidebar/person.svg";
import { ReactComponent as Timeline } from "src/components/AppLayoutWithSidebar/timeline.svg";
import { DisabledItem } from "src/components/DisabledItem";
import LinkExternal from "src/components/LinkExternal";
import { LinkNav } from "src/components/LinkNav";
import LinkNavSummary from "src/components/LinkNavSummary";
import SidebarActions from "src/components/SidebarActions";
import { useOutcomes } from "src/hooks";
import { ReactComponent as ChevronLeft } from "src/images/chevron-left.svg";
import { humanDate } from "src/lib/dateUtils";
import { StatusCheck } from "src/lib/experiment";
import { OutcomesList } from "src/lib/types";
import { AnalysisData, MetadataPoint } from "src/lib/visualization/types";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

export const RESULTS_LOADING_TEXT = "Checking results availability...";
export const RESULTS_WAITING_FOR_LAUNCH_TEXT =
  "Waiting for experiment to launch";

export const editPages = [
  {
    name: "Audience",
    slug: "audience",
    icon: <Person className="sidebar-icon" />,
  },
];

const analysisLinkProps = {
  textColor: "inherit-color",
  className: "mx-1 mb-2 ml-3",
};

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
      newMap[metric] =
        metricsMetaData[metric]?.friendly_name || otherMetrics[group][metric];
    });
  });
  return newMap;
};

type AppLayoutSidebarLaunchedProps = {
  testid?: string;
  children: React.ReactNode;
  status: StatusCheck;
  analysis?: AnalysisData;
  analysisRequired?: boolean; // the page and sidebar need analysis data
  analysisError?: Error;
  experiment: getExperiment_experimentBySlug;
  refetch?: () => Promise<any>;
} & RouteComponentProps;

export const AppLayoutSidebarLaunched = ({
  children,
  testid = "AppLayoutSidebarLaunched",
  status,
  analysis,
  analysisRequired,
  analysisError,
  experiment,
  refetch = async () => {},
}: AppLayoutSidebarLaunchedProps) => {
  const { slug } = useParams();
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
      if (analysisRequired) {
        return (
          <li className="ml-4 mb-2" key={metrics[sidebarKey]}>
            <a
              href={`#${sidebarKey}`}
              className="inherit-color font-weight-normal"
            >
              {metrics[sidebarKey]}
            </a>
          </li>
        );
      }
      return (
        <LinkNav
          key={metrics[sidebarKey]}
          route={`${slug}/results#${sidebarKey}`}
          textColor="inherit-color"
          className="font-weight-normal ml-4 mb-2"
        >
          {metrics[sidebarKey]}
        </LinkNav>
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
      <LinkNav route={`${slug}/results`} testid="nav-results">
        <BarChart className="sidebar-icon" />
        Results
      </LinkNav>
      <li>
        <ul className="text-dark list-unstyled ml-4">
          <LinkNav route={`${slug}/results#overview`} {...analysisLinkProps}>
            Overview
          </LinkNav>
          <LinkNav
            route={`${slug}/results#results_summary`}
            {...analysisLinkProps}
          >
            Results Summary
          </LinkNav>
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

  return (
    <Container fluid className="h-100vh" data-testid={testid}>
      <Row className="h-md-100">
        <Col
          md="3"
          lg="3"
          xl="2"
          className="bg-light pt-2 border-right shadow-sm"
        >
          <nav data-testid="nav-sidebar" className="navbar">
            <Nav
              className="flex-column font-weight-semibold mx-2 w-100"
              as="ul"
            >
              <LinkNav
                className="mb-3 small font-weight-bold"
                textColor="text-secondary"
              >
                <ChevronLeft className="ml-n1" width="18" height="18" />
                Back to Experiments
              </LinkNav>

              <LinkNavSummary
                {...{ status, slug }}
                canReview={experiment.canReview}
              />

              <LinkNav
                route={`/history/${slug}`}
                testid={`history-page-${slug}`}
                relativeToRoot
                useButton
              >
                <Timeline className="sidebar-icon" />
                History
              </LinkNav>

              {experiment.isRollout &&
                experiment.status !== "COMPLETE" &&
                editPages.map((page, idx) => (
                  <LinkNav
                    key={`sidebar-${page.name}-${idx}`}
                    route={`${slug}/${page.slug}`}
                    testid={`nav-edit-audience`}
                  >
                    {page.icon}
                    {page.name}
                  </LinkNav>
                ))}

              {experiment.showResultsUrl ? (
                <ResultsAvailableNav />
              ) : (
                <DisabledItem name="Results" testId="show-no-results">
                  {!status.launched && (status.waiting || status.approved) ? (
                    RESULTS_WAITING_FOR_LAUNCH_TEXT
                  ) : analysisError ? (
                    <>
                      Could not get visualization data. Please contact data
                      science in{" "}
                      <LinkExternal href="https://mozilla.slack.com/archives/CF94YGE03">
                        #ask-experimenter
                      </LinkExternal>
                      .
                    </>
                  ) : analysis?.metadata?.external_config?.skip ? (
                    "Experiment analysis was skipped"
                  ) : (
                    <>
                      Experiment analysis not ready yet.
                      {experiment.resultsExpectedDate && (
                        <>
                          {" "}
                          Results expected{" "}
                          <b>{humanDate(experiment.resultsExpectedDate)}</b>.
                        </>
                      )}
                    </>
                  )}
                </DisabledItem>
              )}

              <SidebarActions {...{ experiment, refetch, status, analysis }} />
            </Nav>
          </nav>
        </Col>
        <Col className="ml-auto mr-auto col-md-9 col-xl-10 pt-5 px-md-3 px-lg-5">
          <main className=" mx-auto p-2 ">{children}</main>
        </Col>
      </Row>
    </Container>
  );
};

export default AppLayoutSidebarLaunched;
