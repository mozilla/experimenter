/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useQuery } from "@apollo/client";
import { Redirect, RouteComponentProps, Router } from "@reach/router";
import React from "react";
import ExperimentRoot from "src/components/App/ExperimentRoot";
import PageEditAudience from "src/components/PageEditAudience";
import PageEditBranches from "src/components/PageEditBranches";
import PageEditMetrics from "src/components/PageEditMetrics";
import PageEditOverview from "src/components/PageEditOverview";
import PageHome from "src/components/PageHome";
import PageLoading from "src/components/PageLoading";
import PageNew from "src/components/PageNew";
import PageResults from "src/components/PageResults";
import PageSummary from "src/components/PageSummary";
import { GET_CONFIG_QUERY } from "src/gql/config";
import { SearchParamsStateProvider, useRefetchOnError } from "src/hooks";
import { BASE_PATH } from "src/lib/constants";

type RootProps = {
  children: React.ReactNode;
} & RouteComponentProps;

type SummaryRootProps = {
  children: React.ReactNode;
} & RouteComponentProps;

const Root = (props: RootProps) => <>{props.children}</>;
const SummaryRoot = (props: SummaryRootProps) => <>{props.children}</>;

const App = () => {
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
      <Router basepath={BASE_PATH}>
        <PageHome path="/" />
        <PageNew path="new" />
        <ExperimentRoot path=":slug">
          <SummaryRoot path="/">
            <Redirect from="/" to="summary" noThrow />
            <PageSummary path="summary" />
            <PageEditAudience path="audience" />
          </SummaryRoot>
          <Root path="edit">
            <Redirect from="/" to="overview" noThrow />
            <PageEditOverview path="overview" />
            <PageEditBranches path="branches" />
            <PageEditMetrics path="metrics" />
            <PageEditAudience path="audience" />
          </Root>
          <PageResults path="results" />
        </ExperimentRoot>
      </Router>
    </SearchParamsStateProvider>
  );
};

export default App;
