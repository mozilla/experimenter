/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useQuery } from "@apollo/client";
import { Redirect, RouteComponentProps, Router } from "@reach/router";
import React from "react";
import { GET_CONFIG_QUERY } from "../../gql/config";
import PageEditAudience from "../PageEditAudience";
import PageEditBranches from "../PageEditBranches";
import PageEditMetrics from "../PageEditMetrics";
import PageEditOverview from "../PageEditOverview";
import PageHome from "../PageHome";
import PageLoading from "../PageLoading";
import PageNew from "../PageNew";
import PageResults from "../PageResults";
import PageSummary from "../PageSummary";

type RootProps = {
  children: React.ReactNode;
} & RouteComponentProps;

const Root = (props: RootProps) => <>{props.children}</>;

const App = ({ basepath }: { basepath: string }) => {
  const { loading } = useQuery(GET_CONFIG_QUERY);

  if (loading) {
    return <PageLoading />;
  }

  return (
    <Router {...{ basepath }}>
      <PageHome path="/" />
      <PageNew path="new" />
      <PageSummary path=":slug" />
      <Root path=":slug/edit">
        <Redirect from="/" to="overview" noThrow />
        <PageEditOverview path="overview" />
        <PageEditBranches path="branches" />
        <PageEditMetrics path="metrics" />
        <PageEditAudience path="audience" />
      </Root>
      <PageResults path=":slug/results" />
    </Router>
  );
};

export default App;
