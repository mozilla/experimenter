/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { navigate, RouteComponentProps } from "@reach/router";
import React, { useCallback, useState } from "react";
import AppLayout from "../AppLayout";
import Head from "../Head";
import { useQuery } from "@apollo/client";
import { Alert, Tab, Tabs } from "react-bootstrap";
import { GET_EXPERIMENTS_QUERY } from "../../gql/experiments";
import {
  useConfig,
  useRefetchOnError,
  useSearchParamsState,
} from "../../hooks";
import DirectoryTable, {
  DirectoryCompleteTable,
  DirectoryDraftsTable,
  DirectoryLiveTable,
} from "./DirectoryTable";
import { getAllExperiments_experiments } from "../../types/getAllExperiments";
import PageLoading from "../PageLoading";
import {
  filterExperiments,
  getFilterValueFromParams,
  updateParamsFromFilterValue,
} from "./filterExperiments";
import sortByStatus from "./sortByStatus";
import { FilterOptions, FilterValue } from "./types";

const PageReporting: React.FunctionComponent<RouteComponentProps> = () => {
  return (
    <AppLayout testid="PageReporting">
      <Head title="Reporting!" />

      <div className="d-flex justify-content-between">
        <h1 className="h2">Reporting!</h1>

      </div>

      <Body />

    </AppLayout>
  );
};

// const { application, num_in_release, num_with_kpi_impact, cdou, other_business_goals } = sortByStatus(
  // filterExperiments(data.experiments, filterValue),
// );



export const Body = () => {
  const { data, loading, error, refetch } = useQuery<{
    experiments: getAllExperiments_experiments[];
  }>(GET_EXPERIMENTS_QUERY, { fetchPolicy: "network-only" });

  // const filterValue = getFilterValueFromParams(config, searchParams);
  // const onFilterChange = (newFilterValue: FilterValue) =>
  //   updateParamsFromFilterValue(updateSearchParams, newFilterValue);

  if (!data) {
    return <div>No experiments found.</div>;
  }
  const { complete } = sortByStatus(
    data.experiments
  );
  // const filterOptions: FilterOptions = {
  //   channels: config!.channels!
  // };
  // const filterValue = getFilterValueFromParams(config);

  return (
    <>
      <Tabs >
        <Tab eventKey="drafts" title={`Application`}>
          <DirectoryTable experiments={complete} />
        </Tab>
      </Tabs>
    </>
  );
};

export default PageReporting;
