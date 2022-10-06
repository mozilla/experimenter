/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useQuery } from "@apollo/client";
import { Link, RouteComponentProps } from "@reach/router";
import React, { useCallback } from "react";
import { Alert, Col, Row, Tab, Tabs } from "react-bootstrap";
import { GET_EXPERIMENTS_QUERY } from "../../gql/experiments";
import {
  useConfig,
  useRefetchOnError,
  useSearchParamsState,
} from "../../hooks";
import { ReactComponent as DownloadIcon } from "../../images/download.svg";
import { getAllExperiments_experiments } from "../../types/getAllExperiments";
import AppLayout from "../AppLayout";
import Head from "../Head";
import LinkExternal from "../LinkExternal";
import PageLoading from "../PageLoading";
import DirectoryTable from "./DirectoryTable";
import FilterBar from "./FilterBar";
import {
  filterExperiments,
  getFilterValueFromParams,
  updateParamsFromFilterValue,
} from "./filterExperiments";
import sortByStatus from "./sortByStatus";
import { FilterOptions, FilterValue } from "./types";

type PageHomeProps = Record<string, any> & RouteComponentProps;

const PageHome: React.FunctionComponent<PageHomeProps> = () => {
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
    allFeatureConfigs: config!.allFeatureConfigs!,
    firefoxVersions: config!.firefoxVersions!,
    owners: config!.owners!,
    channels: config!.channels,
    types: config!.types,
  };

  const { live, complete, preview, review, draft, archived } = sortByStatus(
    filterExperiments(data.experiments, filterValue),
  );

  return (
    <AppLayout testid="PageHome">
      <Head title="Experiments" />
      <h2 className="mb-3 text-center">Nimbus Experiments </h2>
      <Row>
        <Col
          md="3"
          lg="3"
          xl="2"
          className="bg-light pt-2 border-right shadow-sm"
        >
          <div className="d-flex mb-4 justify-content-between flex-column">
            <div>
              <a
                href={`/api/v5/csv`}
                className="btn btn-secondary btn-small ml-2"
                data-testid="reports-anchor"
              >
                <DownloadIcon
                  width="20"
                  height="20"
                  fill="white"
                  dominantBaseline="start"
                  role="img"
                  aria-label="download icon"
                />
                <span> Reports</span>
              </a>
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
            <div>
              <span role="img" aria-label="book emoji">
                📖
              </span>{" "}
              Not sure where to start? Check out the{" "}
              <LinkExternal href="https://experimenter.info">
                Experimenter documentation hub.
              </LinkExternal>
            </div>
            <div>
              <span role="img" aria-label="magnifying emoji">
                🔍
              </span>{" "}
              Looking for the old Experimenter?{" "}
              <LinkExternal href="/legacy" id="legacy_page_link">
                It&lsquo;s still here!
              </LinkExternal>
              <span role="img" aria-label="magnifying emoji">
                💡
              </span>{" "}
              Have feedback?{" "}
              <LinkExternal href="https://mozilla-hub.atlassian.net/secure/CreateIssueDetails!init.jspa?pid=10203&amp;issuetype=10097">
                Please file it here!
              </LinkExternal>
            </div>
          </Alert>
          <FilterBar
            {...{
              options: filterOptions,
              value: filterValue,
              onChange: onFilterChange,
            }}
          />
        </Col>
        <Col md="9" lg="9" xl="10">
          <Tabs activeKey={selectedTab} onSelect={onSelectTab}>
            <Tab eventKey="live" title={`Live (${live.length})`}>
              <DirectoryTable experiments={live} />
            </Tab>

            <Tab eventKey="review" title={`Review (${review.length})`}>
              <DirectoryTable experiments={review} />
            </Tab>

            <Tab eventKey="preview" title={`Preview (${preview.length})`}>
              <DirectoryTable experiments={preview} />
            </Tab>

            <Tab eventKey="completed" title={`Completed (${complete.length})`}>
              <DirectoryTable experiments={complete} />
            </Tab>

            <Tab eventKey="drafts" title={`Draft (${draft.length})`}>
              <DirectoryTable experiments={draft} />
            </Tab>

            <Tab eventKey="archived" title={`Archived (${archived.length})`}>
              <DirectoryTable experiments={archived} />
            </Tab>
          </Tabs>
        </Col>
      </Row>
    </AppLayout>
  );
};

export default PageHome;
