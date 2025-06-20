/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useQuery } from "@apollo/client";
import { Router } from "@reach/router";
import React from "react";
import ExperimentRoot from "src/components/App/ExperimentRoot";
import PageLoading from "src/components/PageLoading";
import PageResults from "src/components/PageResults";
import { GET_CONFIG_QUERY } from "src/gql/config";
import { useRefetchOnError } from "src/hooks";
import { BASE_PATH } from "src/lib/constants";

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
    <>
      <Router basepath={BASE_PATH}>
        <ExperimentRoot path=":slug">
          <PageResults path="results" />
        </ExperimentRoot>
      </Router>
    </>
  );
};

export default App;
