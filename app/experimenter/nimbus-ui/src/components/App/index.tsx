/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { Router, Redirect, RouteComponentProps } from "@reach/router";
import { useQuery } from "@apollo/client";
import { GET_CONFIG_QUERY } from "../../gql/config";
import PageLoading from "../PageLoading";
import PageHome from "../PageHome";
import PageNew from "../PageNew";
import PageSummary from "../PageSummary";
import PageDesign from "../PageDesign";
import PageResults from "../PageResults";
import PageEditOverview from "../PageEditOverview";
import PageEditBranches from "../PageEditBranches";
import PageEditMetrics from "../PageEditMetrics";
import PageEditAudience from "../PageEditAudience";
import PageRequestReview from "../PageRequestReview";

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
      <PageRequestReview path=":slug/request-review" />
      <PageDesign path=":slug/design" />
      <PageResults path=":slug/results" />
    </Router>
  );
};

export default App;
