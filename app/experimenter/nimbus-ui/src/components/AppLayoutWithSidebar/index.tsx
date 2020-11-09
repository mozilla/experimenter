/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps, useParams, Link } from "@reach/router";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Nav from "react-bootstrap/Nav";
import { BASE_PATH } from "../../lib/constants";
import classNames from "classnames";

type AppLayoutWithSidebarProps = {
  testid?: string;
  children: React.ReactNode;
} & RouteComponentProps;

export const AppLayoutWithSidebar = ({
  children,
  testid = "AppLayoutWithSidebar",
}: AppLayoutWithSidebarProps) => {
  const { slug } = useParams();
  return (
    <Container fluid className="h-100vh" data-testid={testid}>
      <Row className="h-md-100">
        <Col
          md="3"
          lg="3"
          xl="2"
          className="bg-light pt-2 border-right shadow-sm"
        >
          <nav data-testid="sidebarNav">
            <Nav className="flex-column" as="ul">
              <LinkNav storiesOf="pages/Home" className="mb-2">
                Experiments
              </LinkNav>
              <LinkNav
                route={`${slug}/edit/overview`}
                storiesOf="pages/EditOverview"
                testid="nav-edit-overview"
              >
                Overview
              </LinkNav>
              <LinkNav
                route={`${slug}/edit/branches`}
                storiesOf="pages/EditBranches"
                testid="nav-edit-branches"
              >
                Branches
              </LinkNav>
              <LinkNav
                route={`${slug}/edit/metrics`}
                storiesOf="pages/EditMetrics"
                testid="nav-edit-metrics"
              >
                Metrics
              </LinkNav>
              <LinkNav
                route={`${slug}/edit/audience`}
                storiesOf="pages/EditAudience"
                testid="nav-edit-audience"
              >
                Audience
              </LinkNav>
              <LinkNav
                route={`${slug}/request-review`}
                storiesOf="pages/RequestReview"
                testid="nav-request-review"
              >
                Review &amp; Launch
              </LinkNav>
            </Nav>
          </nav>
        </Col>
        <Col className="ml-auto mr-auto col-md-9 col-xl-10 pt-5 px-md-3 px-lg-5">
          <main>{children}</main>
        </Col>
      </Row>
    </Container>
  );
};

type LinkNavProps = {
  children: React.ReactNode;
  route?: string;
  storiesOf: string;
  testid?: string;
  className?: string;
};

const LinkNav = ({
  route,
  children,
  storiesOf,
  testid = "nav-home",
  className,
}: LinkNavProps) => {
  const to = route ? `${BASE_PATH}/${route}` : BASE_PATH;
  // an alternative to reach-router's `isCurrent` with identical
  // functionality; explicitely setting it here allows us to test.
  // eslint-disable-next-line
  const isCurrentPage = location.pathname === to;
  return (
    <Nav.Item as="li" className={classNames("m-1", className)}>
      <Link
        {...{ to }}
        data-sb-kind={storiesOf}
        className={isCurrentPage ? "text-primary" : "text-dark"}
        data-testid={testid}
      >
        {children}
      </Link>
    </Nav.Item>
  );
};

export default AppLayoutWithSidebar;
