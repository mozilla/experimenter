/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Router, Redirect, RouteComponentProps } from "@reach/router";

import { BASE_PATH } from "../../lib/constants";
import PageHome from "../PageHome";
import PageNew from "../PageNew";
import PageEditOverview from "../PageEditOverview";
import PageEditBranches from "../PageEditBranches";
import PageRequestReview from "../PageRequestReview";

type RootProps = {
  children: React.ReactNode;
} & RouteComponentProps;

const Root = (props: RootProps) => <>{props.children}</>;

const App = ({ basepath }: { basepath: string }) => {
  return (
    <Router {...{ basepath }}>
      <PageHome path="/" />
      <PageNew path="new" />
      <Root path=":slug/edit">
        <Redirect from="/" to="overview" noThrow />
        <PageEditOverview path="overview" />
        <PageEditBranches path="branches" />
      </Root>
      <PageRequestReview path=":slug/request-review" />
    </Router>
  );
};

export default App;
