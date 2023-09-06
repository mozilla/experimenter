/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps, useParams } from "@reach/router";
import React from "react";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Row from "react-bootstrap/Row";
import { ReactComponent as ChartArrow } from "src/components/AppLayoutWithSidebar/chart-arrow.svg";
import { ReactComponent as Cog } from "src/components/AppLayoutWithSidebar/cog.svg";
import "src/components/AppLayoutWithSidebar/index.scss";
import { ReactComponent as Layers } from "src/components/AppLayoutWithSidebar/layers.svg";
import { ReactComponent as Person } from "src/components/AppLayoutWithSidebar/person.svg";
import { ReactComponent as Timeline } from "src/components/AppLayoutWithSidebar/timeline.svg";
import { LinkNav } from "src/components/LinkNav";
import LinkNavSummary from "src/components/LinkNavSummary";
import SidebarActions from "src/components/SidebarActions";
import { useReviewCheck } from "src/hooks";
import { ReactComponent as ChevronLeft } from "src/images/chevron-left.svg";
import { getStatus } from "src/lib/experiment";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";

type AppLayoutWithSidebarProps = {
  testid?: string;
  children: React.ReactNode;
  experiment: getExperiment_experimentBySlug;
  refetch?: () => Promise<any>;
} & RouteComponentProps;

export const editPages = [
  {
    name: "Overview",
    slug: "overview",
    icon: <Cog className="sidebar-icon" />,
  },
  {
    name: "Branches",
    slug: "branches",
    icon: <Layers className="sidebar-icon" />,
  },
  {
    name: "Metrics",
    slug: "metrics",
    icon: <ChartArrow className="sidebar-icon" />,
  },
  {
    name: "Audience",
    slug: "audience",
    icon: <Person className="sidebar-icon" />,
  },
];

export const AppLayoutWithSidebar = ({
  children,
  testid = "AppLayoutWithSidebar",
  experiment,
  refetch = async () => {},
}: AppLayoutWithSidebarProps) => {
  const { slug } = useParams();
  const { invalidPages, InvalidPagesList } = useReviewCheck(experiment);
  const status = getStatus(experiment);
  const hasMissingDetails = invalidPages.length > 0 && experiment.canEdit;
  let lockedReason: string;
  if (status.review) {
    lockedReason = "in Review";
  } else if (status.preview) {
    lockedReason = "in Preview";
  } else if (experiment.isArchived) {
    lockedReason = "Archived";
  }

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
            <Nav className="flex-column font-weight-semibold w-100" as="ul">
              <LinkNav
                className="mb-3 small font-weight-bold"
                textColor="text-secondary"
              >
                <ChevronLeft className="ml-n1" width="18" height="18" />
                Back to Experiments
              </LinkNav>

              <LinkNavSummary
                {...{ status, slug }}
                showSummaryAction={!hasMissingDetails}
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

              {hasMissingDetails && (
                <div className="mx-1 mb-2 d-flex text-muted font-weight-normal">
                  <div className="sidebar-icon"></div>
                  <p className="my-0 small">
                    Missing details in: <InvalidPagesList />
                  </p>
                </div>
              )}

              <p className="edit-divider position-relative small my-2">
                <span className="position-relative bg-light pl-1 pr-2 text-muted">
                  Edit
                </span>
              </p>

              {editPages.map((page, idx) => (
                <LinkNav
                  key={`sidebar-${page.name}-${idx}`}
                  route={`${slug}/edit/${page.slug}`}
                  testid={`nav-edit-${page.slug}`}
                  title={
                    experiment.canEdit
                      ? undefined
                      : `Experiments cannot be edited while ${lockedReason}`
                  }
                  disabled={!experiment.canEdit}
                >
                  {page.icon}
                  {page.name}
                </LinkNav>
              ))}

              <SidebarActions {...{ experiment, refetch, status }} />
            </Nav>
          </nav>
        </Col>
        <Col className="ml-auto mr-auto col-md-9 col-xl-10 pt-5 px-md-3 px-lg-5">
          <main className="mx-auto p-2">{children}</main>
        </Col>
      </Row>
    </Container>
  );
};

export default AppLayoutWithSidebar;
