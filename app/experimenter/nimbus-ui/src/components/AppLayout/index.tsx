/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Container from "react-bootstrap/Container";

type AppLayoutProps = {
  testid?: string;
  children: React.ReactNode;
};

export const AppLayout = ({ children, testid = "main" }: AppLayoutProps) => {
  return (
    <Container
      fluid
      as="main"
      className="h-100 pt-5"
      data-testid={testid}
      id={testid + "-page"}
    >
      <div className="h-100 container-lg mx-auto">{children}</div>
    </Container>
  );
};

export default AppLayout;
