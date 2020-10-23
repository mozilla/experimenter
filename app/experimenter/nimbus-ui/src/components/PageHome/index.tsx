/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import AppLayout from "../AppLayout";
import { RouteComponentProps, Link } from "@reach/router";

type PageHomeProps = {} & RouteComponentProps;

const PageHome = (props: PageHomeProps) => (
  <AppLayout testid="PageHome">
    <h1>Home</h1>
    <Link to="./new" data-sb-kind="pages/New">
      New experiment
    </Link>
  </AppLayout>
);

export default PageHome;
