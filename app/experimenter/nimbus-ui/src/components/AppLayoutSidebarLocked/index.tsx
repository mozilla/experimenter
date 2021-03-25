import { RouteComponentProps, useParams } from "@reach/router";
import React from "react";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Row from "react-bootstrap/Row";
import Scrollspy from "react-scrollspy";
import { useOutcomes } from "../../hooks";
import { ReactComponent as Airplane } from "../../images/airplane.svg";
import { ReactComponent as ChevronLeft } from "../../images/chevron-left.svg";
import { StatusCheck } from "../../lib/experiment";
import { OutcomesList } from "../../lib/types";
import { AnalysisData, MetadataPoint } from "../../lib/visualization/types";
import { analysisAvailable } from "../../lib/visualization/utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { DisabledItem } from "../DisabledItem";
import LinkExternal from "../LinkExternal";
import { LinkNav } from "../LinkNav";
import { ReactComponent as BarChart } from "./bar-chart.svg";

export const RESULTS_LOADING_TEXT = "Checking results availability...";

const analysisNotRequiredLinkProps = {
  storiesOf: "pages/Results",
  textColor: "inherit-color",
  className: "mx-1 mb-2 ml-3",
};

const outcomeToMapping = (outcomes: OutcomesList) => {
  return outcomes.reduce((acc: { [key: string]: string }, outcome) => {
    acc[outcome?.slug as string] = outcome?.friendlyName!;
    return acc;
  }, {});
};

const otherMetricsToFriendlyName = (
  otherMetrics: { [metric: string]: string },
  metricsMetaData: { [metric: string]: MetadataPoint },
) => {
  const newMap: { [key: string]: string } = {};
  Object.keys(otherMetrics).map(
    (metric) =>
      (newMap[metric] =
        metricsMetaData[metric]?.friendly_name || otherMetrics[metric]),
  );
  return newMap;
};

type AppLayoutSidebarLockedProps = {
  testid?: string;
  children: React.ReactNode;
  status: StatusCheck;
  analysis?: AnalysisData;
  analysisRequired?: boolean; // the page and sidebar need analysis data
  analysisLoadingInSidebar?: boolean; // only the sidebar needs analysis data & is loading
  analysisError?: Error;
  experiment: getExperiment_experimentBySlug;
} & RouteComponentProps;

export const AppLayoutSidebarLocked = ({
  children,
  testid = "AppLayoutSidebarLocked",
  status,
  analysis,
  analysisRequired,
  analysisLoadingInSidebar = false,
  analysisError,
  experiment,
}: AppLayoutSidebarLockedProps) => {
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
          storiesOf="pages/Results"
          textColor="inherit-color"
          className="font-weight-normal ml-4 mb-2"
        >
          {metrics[sidebarKey]}
        </LinkNav>
      );
    });

    // Semantically speaking, nested items should be wrapped in another `<ul>`
    // but Scrollspy doesn't work as of 3.4.3 so all links are top-level under
    // a single `<ul>`
    sidebarItems.unshift(
      <li key={title} className="mb-2 ml-3">
        {title}
      </li>,
    );
    return sidebarItems;
  };

  const sidebarKeys = [
    "monitoring",
    "overview",
    "results_summary",
    "primary_metrics",
  ]
    .concat(Object.keys(primaryMetrics || []))
    .concat("secondary_metrics")
    .concat(Object.keys(secondaryMetrics || []))
    .concat("default_metrics")
    .concat(Object.keys(otherMetrics || []));

  const ResultsAvailableNav = () => (
    <>
      <LinkNav
        route={`${slug}/results`}
        storiesOf="pages/Results"
        testid="nav-results"
      >
        <BarChart className="sidebar-icon" />
        Results
      </LinkNav>
      <li>
        {/* We only need Scrollspy when analysis data is required on the page */}
        {analysisRequired ? (
          <Scrollspy
            items={sidebarKeys}
            className="text-dark list-unstyled ml-4"
            currentClassName="text-primary"
          >
            {/* NOTE: Scrollspy (as of 3.4.3) has caused serious headache while trying to DRY
              this section up as it doesn't play nice with React fragments or even with a component
              conditionally returning `<LinkNav` or `<a href`. If you're refactoring here,
              check early on that Scrollspy still works. */}
            <li className="ml-3 mb-2">
              <a href="#monitoring" className="inherit-color">
                Monitoring
              </a>
            </li>
            <li className="ml-3 mb-2">
              <a href="#overview" className="inherit-color">
                Overview
              </a>
            </li>
            <li className="ml-3 mb-2">
              <a href="#results_summary" className="inherit-color">
                Results Summary
              </a>
            </li>

            {Object.keys(primaryMetrics).length > 0 &&
              getNestedSidebarItems(primaryMetrics, "Primary Metrics")}
            {Object.keys(secondaryMetrics).length > 0 &&
              getNestedSidebarItems(secondaryMetrics, "Secondary Metrics")}
            {otherMetrics &&
              analysis?.overall &&
              getNestedSidebarItems(otherMetrics, "Default Metrics")}
          </Scrollspy>
        ) : (
          <ul className="text-dark list-unstyled ml-4">
            <LinkNav
              route={`${slug}/results#monitoring`}
              {...analysisNotRequiredLinkProps}
            >
              Monitoring
            </LinkNav>

            <LinkNav
              route={`${slug}/results#overview`}
              {...analysisNotRequiredLinkProps}
            >
              Overview
            </LinkNav>

            <LinkNav
              route={`${slug}/results#results_summary`}
              {...analysisNotRequiredLinkProps}
            >
              Results Summary
            </LinkNav>

            {Object.keys(primaryMetrics).length > 0 &&
              getNestedSidebarItems(primaryMetrics, "Primary Metrics")}
            {Object.keys(secondaryMetrics).length > 0 &&
              getNestedSidebarItems(secondaryMetrics, "Secondary Metrics")}
            {otherMetrics &&
              analysis?.overall &&
              getNestedSidebarItems(otherMetrics, "Default Metrics")}
          </ul>
        )}
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
          <nav
            data-testid="nav-sidebar"
            className="navbar fixed-top col-xl-2 col-lg-3 col-md-3 px-4 py-3"
          >
            <Nav
              className="flex-column font-weight-semibold mx-2 w-100"
              as="ul"
            >
              <LinkNav
                storiesOf="pages/Home"
                className="mb-3 small font-weight-bold"
                textColor="text-secondary"
              >
                <ChevronLeft className="ml-n1" width="18" height="18" />
                Experiments
              </LinkNav>
              <LinkNav
                route={slug}
                storiesOf="pages/Summary"
                testid="nav-summary"
              >
                <Airplane className="sidebar-icon" />
                Summary
              </LinkNav>
              {analysisAvailable(analysis) ? (
                <ResultsAvailableNav />
              ) : (
                <DisabledItem name="Results" testId="show-no-results">
                  {status?.accepted ? (
                    "Waiting for experiment to launch"
                  ) : analysisLoadingInSidebar ? (
                    RESULTS_LOADING_TEXT
                  ) : analysisError ? (
                    <>
                      Could not get visualization data. Please contact data
                      science in{" "}
                      <LinkExternal href="https://mozilla.slack.com/archives/C0149JH7C1M">
                        #cirrus
                      </LinkExternal>
                      .
                    </>
                  ) : (
                    "Experiment results not yet ready"
                  )}
                </DisabledItem>
              )}
            </Nav>
          </nav>
        </Col>
        <Col className="ml-auto mr-auto col-md-9 col-xl-10 pt-5 px-md-3 px-lg-5">
          <main className="container-lg mx-auto">{children}</main>
        </Col>
      </Row>
    </Container>
  );
};

export default AppLayoutSidebarLocked;
