/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useQuery } from "@apollo/client";
import { Redirect, RouteComponentProps, Router } from "@reach/router";
import React from "react";
import { GET_CONFIG_QUERY } from "../../gql/config";
import { SearchParamsStateProvider, useRefetchOnError } from "../../hooks";
import PageEditAudience from "../PageEditAudience";
import PageEditBranches from "../PageEditBranches";
import PageEditMetrics from "../PageEditMetrics";
import PageEditOverview from "../PageEditOverview";
import PageHome from "../PageHome";
import PageLoading from "../PageLoading";
import PageNew from "../PageNew";
import PageResults from "../PageResults";
import PageSummary from "../PageSummary";
import PageSummaryDetail from "../PageSummaryDetails";

type RootProps = {
  children: React.ReactNode;
} & RouteComponentProps;

const Root = (props: RootProps) => <>{props.children}</>;

const App = ({ basepath }: { basepath: string }) => {
  const { loading, error, refetch } = useQuery(GET_CONFIG_QUERY);
  const ErrorAlert = useRefetchOnError(error, refetch, "mt-0");

  if (loading) {
    return <PageLoading />;
  }

  if (error) {
    return ErrorAlert;
  }

  return (
    <SearchParamsStateProvider>
      <Router {...{ basepath }}>
        <PageHome path="/" />
        <PageNew path="new" />
        <PageSummary path=":slug" />
        <PageSummaryDetail path=":slug/details" />
        <Root path=":slug/edit">
          <Redirect from="/" to="overview" noThrow />
          <PageEditOverview path="overview" />
          <PageEditBranches path="branches" />
          <PageEditMetrics path="metrics" />
          <PageEditAudience path="audience" />
        </Root>
        <PageResults path=":slug/results" />
      </Router>
    </SearchParamsStateProvider>
  );
};

export default App;
