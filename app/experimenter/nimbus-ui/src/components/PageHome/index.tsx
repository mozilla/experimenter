/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import AppLayout from "../AppLayout";
import { RouteComponentProps, Link } from "@reach/router";
import Head from "../Head";

type PageHomeProps = {} & RouteComponentProps;

const PageHome: React.FunctionComponent<PageHomeProps> = () => (
  <AppLayout testid="PageHome">
    <Head title="Experiments" />

    <h1>Home</h1>
    <Link to="new" data-sb-kind="pages/New">
      New experiment
    </Link>
  </AppLayout>
);

export default PageHome;
