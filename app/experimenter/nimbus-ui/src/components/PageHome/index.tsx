/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import AppLayout from "../AppLayout";
import { RouteComponentProps, Link } from "@reach/router";
import Head from "../Head";
import { useQuery } from "@apollo/client";
import { getAllExperiments_experiments } from "../../types/getAllExperiments";
import { GET_ALL_EXPERIMENTS } from "../../gql/experiments";
import PageLoading from "../PageLoading";
import sortByStatus from "./sortByStatus";
import DirectoryTable, {
  DirectoryLiveTable,
  DirectoryCompleteTable,
  DirectoryDraftsTable,
} from "../DirectoryTable";

type PageHomeProps = {} & RouteComponentProps;

export const Body = () => {
  const { data, loading } = useQuery<{
    experiments: getAllExperiments_experiments[];
  }>(GET_ALL_EXPERIMENTS);

  if (loading) {
    return <PageLoading />;
  }

  if (!data) {
    return <div>No experiments found.</div>;
  }

  const { live, complete, review, draft } = sortByStatus(data.experiments);
  return (
    <>
      <DirectoryLiveTable title="Live Experiments" experiments={live} />
      <DirectoryCompleteTable title="Completed" experiments={complete} />
      <DirectoryTable title="In Review" experiments={review} />
      <DirectoryDraftsTable title="Drafts" experiments={draft} />
    </>
  );
};

const PageHome: React.FunctionComponent<PageHomeProps> = () => {
  return (
    <AppLayout testid="PageHome">
      <Head title="Experiments" />

      <h2 className="mb-4">
        Nimbus Experiments{" "}
        <Link
          to="new"
          data-sb-kind="pages/New"
          className="btn btn-primary btn-small ml-2"
        >
          New experiment
        </Link>
      </h2>
      <Body />
    </AppLayout>
  );
};

export default PageHome;
