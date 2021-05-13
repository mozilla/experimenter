/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps, useParams } from "@reach/router";
import React from "react";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Row from "react-bootstrap/Row";
import { useReviewCheck } from "../../hooks";
import { ReactComponent as Airplane } from "../../images/airplane.svg";
import { ReactComponent as ChevronLeft } from "../../images/chevron-left.svg";
import { ReactComponent as Clipboard } from "../../images/clipboard.svg";
import { getStatus } from "../../lib/experiment";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { LinkNav } from "../LinkNav";
import { ReactComponent as ChartArrow } from "./chart-arrow.svg";
import { ReactComponent as Cog } from "./cog.svg";
import "./index.scss";
import { ReactComponent as Layers } from "./layers.svg";
import { ReactComponent as Person } from "./person.svg";

type AppLayoutWithSidebarProps = {
  testid?: string;
  children: React.ReactNode;
  experiment: getExperiment_experimentBySlug;
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
}: AppLayoutWithSidebarProps) => {
  const { slug } = useParams();
  const { invalidPages, InvalidPagesList } = useReviewCheck(experiment);
  const status = getStatus(experiment);
  const reviewOrPreview = !status?.idle || status?.preview;

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
                storiesOf="pages/Home"
                className="mb-3 small font-weight-bold"
                textColor="text-secondary"
              >
                <ChevronLeft className="ml-n1" width="18" height="18" />
                Experiments
              </LinkNav>

              <LinkNav
                route={`${slug}`}
                storiesOf={"pages/Summary"}
                testid={"nav-summary"}
              >
                <Airplane className="sidebar-icon" />
                Summary
              </LinkNav>

              <p className="edit-divider position-relative small mb-2 mt-3">
                <span className="position-relative bg-light pl-1 pr-2 text-muted">
                  Edit Experiment
                </span>
              </p>

              {editPages.map((page, idx) => (
                <LinkNav
                  key={`sidebar-${page.name}-${idx}`}
                  route={`${slug}/edit/${page.slug}`}
                  storiesOf={`pages/Edit${page.name}`}
                  testid={`nav-edit-${page.slug}`}
                  title={
                    reviewOrPreview
                      ? "Experiments cannot be edited while in Review or Preview"
                      : undefined
                  }
                  disabled={reviewOrPreview}
                >
                  {page.icon}
                  {page.name}
                </LinkNav>
              ))}
              <LinkNav
                route={`${slug}/request-review`}
                storiesOf="pages/RequestReview"
                testid="nav-request-review"
              >
                <Clipboard className="sidebar-icon" />
                Review &amp; Launch
              </LinkNav>

              {invalidPages.length > 0 && !reviewOrPreview && (
                <div className="mx-1 mb-2 d-flex text-muted font-weight-normal">
                  <div className="sidebar-icon"></div>
                  <p className="my-0 small">
                    Missing details in: <InvalidPagesList />
                  </p>
                </div>
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

export default AppLayoutWithSidebar;
