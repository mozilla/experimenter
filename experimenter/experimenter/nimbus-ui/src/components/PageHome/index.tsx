/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useQuery } from "@apollo/client";
import { Link, RouteComponentProps } from "@reach/router";
import React, { useCallback, useEffect, useState } from "react";
import { Alert, Col, Container, Row, Tab, Tabs } from "react-bootstrap";
import AppLayout from "src/components/AppLayout";
import Head from "src/components/Head";
import LinkExternal from "src/components/LinkExternal";
import DirectoryTable from "src/components/PageHome/DirectoryTable";
import FilterBar from "src/components/PageHome/FilterBar";
import {
  filterExperiments,
  getFilterValueFromParams,
  updateParamsFromFilterValue,
} from "src/components/PageHome/filterExperiments";
import SearchBar from "src/components/PageHome/SearchBar";
import sortByStatus from "src/components/PageHome/sortByStatus";
import { FilterOptions, FilterValue } from "src/components/PageHome/types";
import PageLoading from "src/components/PageLoading";
import { GET_EXPERIMENTS_QUERY } from "src/gql/experiments";
import { useConfig, useRefetchOnError, useSearchParamsState } from "src/hooks";
import { ReactComponent as DownloadIcon } from "src/images/download.svg";
import { ReactComponent as Logo } from "src/images/logo.svg";
import { ReactComponent as CreateNewIcon } from "src/images/pencil.svg";
import { getAllExperiments_experiments } from "src/types/getAllExperiments";
type PageHomeProps = Record<string, any> & RouteComponentProps;

export type BodyProps = {
  searchedExperiments: getAllExperiments_experiments[];
  loading: any;
  error: any;
  refetch: any;
};

export const Body: React.FC<BodyProps> = ({
  searchedExperiments,
  loading,
  error,
  refetch,
}) => {
  const config = useConfig();
  const [searchParams, updateSearchParams] = useSearchParamsState("PageHome");

  const ErrorAlert = useRefetchOnError(error, refetch);

  const selectedTab = searchParams.get("tab") || "live";
  const onSelectTab = useCallback(
    (nextTab) => updateSearchParams((params) => params.set("tab", nextTab)),
    [updateSearchParams],
  );
  const filterValue = getFilterValueFromParams(config, searchParams);

  if (loading) {
    return <PageLoading />;
  }

  if (error) {
    return ErrorAlert;
  }

  const { live, complete, preview, review, draft, archived } = sortByStatus(
    filterExperiments(searchedExperiments ?? [], filterValue),
  );

  return (
    <>
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
    </>
  );
};

const PageHome: React.FunctionComponent<PageHomeProps> = () => {
  const config = useConfig();
  const [searchParams, updateSearchParams] = useSearchParamsState("PageHome");
  const filterValue = getFilterValueFromParams(config, searchParams);
  const onFilterChange = (newFilterValue: FilterValue) =>
    updateParamsFromFilterValue(updateSearchParams, newFilterValue);

  const filterOptions: FilterOptions = {
    applications: config!.applications!,
    allFeatureConfigs: config!.allFeatureConfigs!,
    firefoxVersions: config!.firefoxVersions!,
    owners: config!.owners!,
    channels: config!.channels,
    types: config!.types,
    projects: config!.projects!,
    targetingConfigs: config!.targetingConfigs,
    takeaways: config!.takeaways,
    qaStatus: config!.qaStatus,
  };

  const { data, loading, error, refetch } = useQuery<{
    experiments: getAllExperiments_experiments[];
  }>(GET_EXPERIMENTS_QUERY, { fetchPolicy: "network-only" });

  const [searchedData, setSearchedData] =
    useState<getAllExperiments_experiments[]>();

  useEffect(() => setSearchedData(data?.experiments), [data]);
  return (
    <AppLayout testid="PageHome">
      <Head title="Experiments" />

      <Logo
        width="100"
        height="85"
        fill="white"
        dominantBaseline="start"
        role="img"
        aria-label="nimbus logo"
        className="float-left pb-1"
      />
      <h2 className="mb-3 text-left pt-4">Nimbus Experiments </h2>
      <Alert variant="primary" className="mb-4 mt-4">
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
          </LinkExternal>{" "}
          <span role="img" aria-label="thinking_face emoji">
            🤔
          </span>{" "}
          Have a question?{" "}
          <LinkExternal href="https://mozilla.slack.com/archives/CF94YGE03">
            Ask us here!.
          </LinkExternal>
        </div>
      </Alert>
      <Container fluid className="h-100vh">
        <Row className="h-md-100">
          <Col
            md="3"
            lg="3"
            xl="2"
            className="bg-light pt-2 border-right shadow-sm"
          >
            <Row>
              <Col>
                <Link
                  to="new"
                  data-sb-kind="pages/New"
                  className="btn btn-primary btn-small mt-2 w-100"
                  id="create-new-button"
                >
                  <CreateNewIcon
                    width="20"
                    height="20"
                    fill="white"
                    dominantBaseline="start"
                    role="img"
                    aria-label="download icon"
                  />
                  <span className="ml-1 pl-1">Create New </span>
                </Link>
              </Col>
            </Row>
            <Row>
              <Col>
                <a
                  href={`/api/v5/csv`}
                  className="btn btn-secondary btn-small mt-3 w-100"
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
              </Col>
            </Row>
            <Row>
              <Col>
                <h5 className="mt-3">{"Filters"}</h5>
                <SearchBar
                  experiments={data?.experiments ?? []}
                  onChange={setSearchedData}
                />
                <FilterBar
                  {...{
                    options: filterOptions,
                    value: filterValue,
                    onChange: onFilterChange,
                  }}
                />
              </Col>
            </Row>
          </Col>
          <Col md="9" lg="9" xl="10">
            <Body
              {...{
                searchedExperiments: searchedData ?? [],
                loading,
                error,
                refetch,
              }}
            />
          </Col>
        </Row>
      </Container>
    </AppLayout>
  );
};

export default PageHome;
