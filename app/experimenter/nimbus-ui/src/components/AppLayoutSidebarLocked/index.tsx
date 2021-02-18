import { RouteComponentProps, useParams } from "@reach/router";
import React from "react";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Row from "react-bootstrap/Row";
import Scrollspy from "react-scrollspy";
import { ReactComponent as ChevronLeft } from "../../images/chevron-left.svg";
import { ReactComponent as Clipboard } from "../../images/clipboard.svg";
import { StatusCheck } from "../../lib/experiment";
import { AnalysisData, MetadataPoint } from "../../lib/visualization/types";
import { analysisAvailable } from "../../lib/visualization/utils";
import {
  getExperiment_experimentBySlug_primaryProbeSets,
  getExperiment_experimentBySlug_secondaryProbeSets,
} from "../../types/getExperiment";
import { DisabledItem } from "../DisabledItem";
import LinkExternal from "../LinkExternal";
import { LinkNav } from "../LinkNav";
import { ReactComponent as BarChart } from "./bar-chart.svg";

export const RESULTS_LOADING_TEXT = "Checking results availability...";

const getSidebarItems = (
  metrics: { [metric: string]: string },
  title: string,
) => {
  const sidebarItems = Object.keys(metrics).map((sidebarKey) => (
    <div key={sidebarKey} className="ml-3">
      <a href={`#${sidebarKey}`} className="inherit-color">
        {metrics[sidebarKey]}
      </a>
    </div>
  ));
  sidebarItems.unshift(
    <h6 key={title} className="font-weight-bold mt-3">
      {title}
    </h6>,
  );
  return sidebarItems;
};

const probesetToMapping = (
  probesets:
    | (getExperiment_experimentBySlug_primaryProbeSets | null)[]
    | (getExperiment_experimentBySlug_secondaryProbeSets | null)[],
) => {
  const newMap: { [key: string]: string } = {};
  probesets.map(
    (
      probeset:
        | (getExperiment_experimentBySlug_primaryProbeSets | null)
        | (getExperiment_experimentBySlug_secondaryProbeSets | null),
    ) => (newMap[probeset!.slug] = probeset!.name),
  );
  return newMap;
};

const otherMetricsToFriendlyName = (
  otherMetrics: { [metric: string]: string },
  metricsMetaData: { [metric: string]: MetadataPoint },
) => {
  const newMap: { [key: string]: string } = {};
  Object.keys(otherMetrics).map(
    (metric) =>
      (newMap[metric] =
        metricsMetaData[metric]!.friendly_name || otherMetrics[metric]),
  );
  return newMap;
};

type AppLayoutSidebarLockedProps = {
  testid?: string;
  children: React.ReactNode;
  status: StatusCheck;
  analysis?: AnalysisData;
  analysisLoadingInSidebar?: boolean;
  analysisError?: Error;
  primaryProbeSets:
    | (getExperiment_experimentBySlug_primaryProbeSets | null)[]
    | null;
  secondaryProbeSets:
    | (getExperiment_experimentBySlug_secondaryProbeSets | null)[]
    | null;
} & RouteComponentProps;

export const AppLayoutSidebarLocked = ({
  children,
  testid = "AppLayoutSidebarLocked",
  status,
  analysis,
  analysisLoadingInSidebar = false,
  analysisError,
  primaryProbeSets,
  secondaryProbeSets,
}: AppLayoutSidebarLockedProps) => {
  const { slug } = useParams();
  const primaryMetrics = probesetToMapping(primaryProbeSets || []);
  const secondaryMetrics = probesetToMapping(secondaryProbeSets || []);
  const otherMetrics = otherMetricsToFriendlyName(
    analysis?.other_metrics || {},
    analysis?.metadata?.metrics || {},
  );

  const sidebarKeys = [
    "monitoring",
    "overview",
    "results-summary",
    "primary-metrics",
  ]
    .concat(Object.keys(primaryMetrics || []))
    .concat("secondary-metrics")
    .concat(Object.keys(secondaryMetrics || []))
    .concat("default-metrics")
    .concat(Object.keys(otherMetrics || []));

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
            className="navbar fixed-top col-xl-2 col-lg-3 col-md-3"
          >
            <Nav className="flex-column font-weight-semibold" as="ul">
              <LinkNav
                storiesOf="pages/Home"
                className="mb-3 small font-weight-bold"
                textColor="text-secondary"
              >
                <ChevronLeft className="ml-n1" width="18" height="18" />
                Experiments
              </LinkNav>
              <LinkNav
                route={`${slug}/design`}
                storiesOf={"pages/Design"}
                testid={"nav-design"}
              >
                <Clipboard className="sidebar-icon" />
                Design
              </LinkNav>
              {analysisAvailable(analysis) ? (
                <>
                  <LinkNav
                    route={`${slug}/results`}
                    storiesOf={"pages/Results"}
                    testid={"nav-results"}
                  >
                    <BarChart className="sidebar-icon" />
                    Results
                  </LinkNav>
                  <Scrollspy
                    items={sidebarKeys}
                    className="text-dark"
                    currentClassName="font-weight-bold text-primary"
                  >
                    <div>
                      <a href="#monitoring" className="inherit-color">
                        Monitoring
                      </a>
                    </div>
                    <div>
                      <a href="#overview" className="inherit-color">
                        Overview
                      </a>
                    </div>
                    <div>
                      <a href="#results-summary" className="inherit-color">
                        Results Summary
                      </a>
                    </div>
                    {Object.keys(primaryMetrics).length &&
                      getSidebarItems(primaryMetrics, "Primary Metrics")}
                    {Object.keys(secondaryMetrics).length &&
                      getSidebarItems(secondaryMetrics, "Secondary Metrics")}
                    {otherMetrics &&
                      getSidebarItems(otherMetrics, "Default Metrics")}
                  </Scrollspy>
                </>
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
