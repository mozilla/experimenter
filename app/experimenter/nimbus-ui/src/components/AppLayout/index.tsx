/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";

type AppLayoutProps = {
  testid?: string;
  children: React.ReactNode;
};

// TODO: Depending on the main page ("directory view") design, we may want two
// AppLayouts - one with a header/footer, and another with a nav sidebar.

export const AppLayout = ({ children, testid = "main" }: AppLayoutProps) => {
  return (
    <Container
      fluid
      as="main"
      className="h-100"
      data-testid={testid}
    >
      <Row className="h-100">
        <Col className="ml-auto mr-auto col-md-10 col-lg-8">
          {children}
        </Col>
      </Row>
    </Container>
  );
};

export default AppLayout;
