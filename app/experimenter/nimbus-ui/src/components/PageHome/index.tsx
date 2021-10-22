/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useQuery } from "@apollo/client";
import { Link, RouteComponentProps } from "@reach/router";
import React, { useCallback } from "react";
import { Alert, Tab, Tabs } from "react-bootstrap";
import { GET_EXPERIMENTS_QUERY } from "../../gql/experiments";
import {
  useConfig,
  useRefetchOnError,
  useSearchParamsState,
} from "../../hooks";
import { getAllExperiments_experiments } from "../../types/getAllExperiments";
import AppLayout from "../AppLayout";
import Head from "../Head";
import LinkExternal from "../LinkExternal";
import PageLoading from "../PageLoading";
import DirectoryTable, {
  DirectoryCompleteTable,
  DirectoryDraftsTable,
  DirectoryLiveTable,
} from "./DirectoryTable";
import FilterBar from "./FilterBar";
import {
  filterExperiments,
  getFilterValueFromParams,
  updateParamsFromFilterValue,
} from "./filterExperiments";
import sortByStatus from "./sortByStatus";
import { FilterOptions, FilterValue } from "./types";

type PageHomeProps = Record<string, any> & RouteComponentProps;

export const Body = () => {
  const config = useConfig();
  const [searchParams, updateSearchParams] = useSearchParamsState("PageHome");
  const { data, loading, error, refetch } = useQuery<{
    experiments: getAllExperiments_experiments[];
  }>(GET_EXPERIMENTS_QUERY, { fetchPolicy: "network-only" });
  const ErrorAlert = useRefetchOnError(error, refetch);

  const selectedTab = searchParams.get("tab") || "live";
  const onSelectTab = useCallback(
    (nextTab) => updateSearchParams((params) => params.set("tab", nextTab)),
    [updateSearchParams],
  );

  const filterValue = getFilterValueFromParams(config, searchParams);
  const onFilterChange = (newFilterValue: FilterValue) =>
    updateParamsFromFilterValue(updateSearchParams, newFilterValue);

  if (loading) {
    return <PageLoading />;
  }

  if (error) {
    return ErrorAlert;
  }

  if (!data) {
    return <div>No experiments found.</div>;
  }

  const filterOptions: FilterOptions = {
    applications: config!.applications!,
    featureConfigs: config!.featureConfigs!,
    firefoxVersions: config!.firefoxVersions!,
    owners: config!.owners!,
  };

  const { live, complete, preview, review, draft, archived } = sortByStatus(
    filterExperiments(data.experiments, filterValue),
  );

  return (
    <>
      <FilterBar
        {...{
          options: filterOptions,
          value: filterValue,
          onChange: onFilterChange,
        }}
      />
      <Tabs activeKey={selectedTab} onSelect={onSelectTab}>
        <Tab eventKey="live" title={`Live (${live.length})`}>
          <DirectoryLiveTable experiments={live} />
        </Tab>
        <Tab eventKey="review" title={`Review (${review.length})`}>
          <DirectoryTable experiments={review} />
        </Tab>
        <Tab eventKey="preview" title={`Preview (${preview.length})`}>
          <DirectoryTable experiments={preview} />
        </Tab>
        <Tab eventKey="completed" title={`Completed (${complete.length})`}>
          <DirectoryCompleteTable experiments={complete} />
        </Tab>
        <Tab eventKey="drafts" title={`Draft (${draft.length})`}>
          <DirectoryDraftsTable experiments={draft} />
        </Tab>
        <Tab eventKey="archived" title={`Archived (${archived.length})`}>
          <DirectoryDraftsTable experiments={archived} />
        </Tab>
      </Tabs>
    </>
  );
};

const PageHome: React.FunctionComponent<PageHomeProps> = () => {
  return (
    <AppLayout testid="PageHome">
      <Head title="Experiments" />

      <div className="d-flex mb-4 justify-content-between">
        <h2 className="mb-0 mr-1">Nimbus Experiments </h2>
        <div>
          <Link
            to="new"
            data-sb-kind="pages/New"
            className="btn btn-primary btn-small ml-2"
            id="create-new-button"
          >
            Create new
          </Link>
        </div>
      </div>

      <Alert variant="primary" className="mb-4">
        <span role="img" aria-label="book emoji">
          📖
        </span>{" "}
        Not sure where to start? Check out the{" "}
        <LinkExternal href="https://experimenter.info">
          Experimenter documentation hub
        </LinkExternal>
        .
      </Alert>

      <Body />
    </AppLayout>
  );
};

export default PageHome;
