/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps } from "@reach/router";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Nav from "react-bootstrap/Nav";

import "./index.scss";

type AppLayoutExperimentEditProps = {
  testid?: string;
  children: React.ReactNode;
} & RouteComponentProps;

export const AppLayoutExperimentEdit = ({
  children,
  testid="main"
}: AppLayoutExperimentEditProps) => {
  return (
    <Container
      fluid
      as="main"
      className="h-100 app-layout-sidebar"
      data-testid={testid}
    >
      <Row className="h-100">
        <Col md="3" lg="3" xl="2" className="bg-light border-right shadow-sm">
          <Nav className="flex-column">
            <SidebarItem>Experiments</SidebarItem>
            <SidebarItem>Overview</SidebarItem>
            <SidebarItem>Branches</SidebarItem>
            <SidebarItem>Metrics</SidebarItem>
            <SidebarItem>Audience</SidebarItem>
            <SidebarItem>Review &amp; Launch</SidebarItem>
          </Nav>
        </Col>
        <Col className="ml-auto mr-auto col-md-10 col-lg-8">
          {children}
        </Col>
      </Row>
    </Container>
  );
};

const SidebarItem = ({ children }: { children: React.ReactNode }) => (
  <Nav.Item className="m-2">{children}</Nav.Item>
);

export default AppLayoutExperimentEdit;
