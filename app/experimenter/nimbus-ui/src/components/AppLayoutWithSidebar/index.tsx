/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps, useParams, Link, LinkProps } from "@reach/router";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Nav from "react-bootstrap/Nav";
import { BASE_PATH } from "../../lib/constants";
import "./index.scss";

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
      <Row className="h-lg-100">
        <Col md="3" lg="3" xl="2" className="bg-light border-right shadow-sm">
          <nav>
            <Nav className="flex-column" as="ul">
              <LinkNav to={BASE_PATH}>Experiments</LinkNav>
              <LinkNav to={`${BASE_PATH}/${slug}/edit/overview`}>
                Overview
              </LinkNav>
              <LinkNav to={`${BASE_PATH}/${slug}/edit/branches`}>
                Branches
              </LinkNav>
              <Nav.Item as="li" className="text-secondary m-1">
                Metrics
              </Nav.Item>
              <Nav.Item as="li" className="text-secondary m-1">
                Audience
              </Nav.Item>
              <LinkNav to={`${BASE_PATH}/${slug}/request-review`}>
                Review &amp; Launch
              </LinkNav>
            </Nav>
          </nav>
        </Col>
        <Col className="ml-auto mr-auto col-md-9 col-xl-10">
          <main>{children}</main>
        </Col>
      </Row>
    </Container>
  );
};

type LinkNavProps = {
  children: React.ReactNode;
  to: string;
};

const LinkNav = ({ to, children }: LinkNavProps) => (
  <Nav.Item as="li" className="m-1">
    <Link
      {...{ to }}
      getProps={({ isCurrent }) => ({
        className: isCurrent ? "text-primary" : "text-dark",
      })}
    >
      {children}
    </Link>
  </Nav.Item>
);

export default AppLayoutWithSidebar;
