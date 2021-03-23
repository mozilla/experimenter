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
  analysisRequired: boolean; // the page and sidebar need analysis data
  analysisLoadingInSidebar?: boolean; // only the sidebar needs analysis data & is loading
  analysisError?: Error;
  experiment: getExperiment_experimentBySlug;
} & RouteComponentProps;

// All link IDs use snake_case over kebab-case for convenience
const convertToLinkId = (title: string) =>
  title.replace(/ /g, "_").toLowerCase();

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

  const getSidebarItems = (
    metrics: { [metric: string]: string },
    title: string,
  ) => (
    <li key={title} className="mb-2">
      <ul className="list-unstyled ml-3">
        <li className="mb-2">{title}</li>
        {Object.keys(metrics).map((sidebarKey) => (
          <NavLink title={metrics[sidebarKey]} key={sidebarKey} {...{sidebarKey}} />
        ))}
      </ul>
    </li>
  );

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

  const NavLink = ({ title, sidebarKey="" }: { title: string, sidebarKey: string }) => (
    <>
      {analysisRequired ? (
        <li className="ml-3 mb-2">
          <a
            href={`#${sidebarKey}`}
            className="font-weight-normal inherit-color"
          >
            {title}
          </a>
        </li>
      ) : (
        <LinkNav
          route={`${slug}/results#${sidebarKey}`}
          storiesOf="pages/Results"
          textColor="inherit-color"
          className="font-weight-normal"
        >
          {title}
        </LinkNav>
      )}
    </>
  );

  const ResultsAvailableNav = () => {
    const nav = (
      <>
        <NavLink title="Monitoring" sidebarKey="monitoring" />
        <NavLink title="Overview" sidebarKey="overview"/>
        <NavLink title="Results Summary" sidebarKey="results_summary"/>

        {Object.keys(primaryMetrics).length > 0 &&
          getSidebarItems(primaryMetrics, "Primary Metrics")}
        {Object.keys(secondaryMetrics).length > 0 &&
          getSidebarItems(secondaryMetrics, "Secondary Metrics")}
        {otherMetrics &&
          analysis?.overall &&
          getSidebarItems(otherMetrics, "Default Metrics")}
      </>
    );
    return (
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
              {nav}
            </Scrollspy>
          ) : (
            <ul className="text-dark list-unstyled ml-4">{nav}</ul>
          )}
        </li>
      </>
    );
  };

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
