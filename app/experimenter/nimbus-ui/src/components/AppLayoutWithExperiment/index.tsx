/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { RouteComponentProps } from "@reach/router";
import React, { useContext } from "react";
import { Alert } from "react-bootstrap";
import { POLL_INTERVAL } from "../../lib/constants";
import { ExperimentContext } from "../../lib/contexts";
import { StatusCheck } from "../../lib/experiment";
import { AnalysisData } from "../../lib/visualization/types";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import AppLayoutSidebarLaunched from "../AppLayoutSidebarLaunched";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import Head from "../Head";
import HeaderExperiment from "../HeaderExperiment";

export type AppLayoutWithExperimentProps = {
  children: React.ReactNode;
  testId?: string;
  title?: string;
  setHead?: boolean; // set the browser tab title through this component
} & RouteComponentProps;

const AppLayoutWithExperiment = ({
  children,
  testId = "AppLayoutWithExperiment",
  title,
  setHead = true,
}: AppLayoutWithExperimentProps) => {
  const {
    slug,
    experiment,
    status,
    analysis,
    analysisError,
    analysisRequired,
    hasPollError,
    refetch,
  } = useContext(ExperimentContext)!;

  const {
    name,
    parent,
    startDate,
    computedEndDate,
    computedDurationDays,
    isArchived,
    isRollout,
  } = experiment;

  return (
    <Layout
      {...{
        children,
        analysisRequired,
        analysis,
        analysisError,
        status,
        experiment,
        refetch,
      }}
    >
      <section data-testid={testId} id={testId}>
        {setHead && (
          <Head
            title={title ? `${experiment.name} – ${title}` : experiment.name}
          />
        )}

        <HeaderExperiment
          {...{
            slug,
            name,
            parent,
            startDate,
            computedEndDate,
            status,
            computedDurationDays,
            isArchived,
            isRollout,
          }}
        />
        {hasPollError && (
          <Alert
            variant="warning"
            data-testid="polling-error-alert"
            className="mt-4"
          >
            <Alert.Heading>Polling Error</Alert.Heading>
            <p>
              This page attempted to poll the server for fresh experiment data
              but ran into an error. This usually happens when Experimenter is
              mid-deploy.
            </p>
            <p>
              Polling will be retried automatically in {POLL_INTERVAL / 1000}{" "}
              seconds.
            </p>
          </Alert>
        )}
        {title && <h2 className="mt-3 mb-4 h3">{title}</h2>}
        <div className="my-4">{children}</div>
      </section>
    </Layout>
  );
};

type LayoutProps = {
  children: React.ReactElement;
  status: StatusCheck;
  analysis?: AnalysisData;
  analysisRequired: boolean;
  analysisError?: Error;
  experiment: getExperiment_experimentBySlug;
  refetch: () => Promise<any>;
};

const Layout = ({
  children,
  status,
  analysis,
  analysisRequired,
  analysisError,
  experiment,
  refetch,
}: LayoutProps) =>
  status?.launched ? (
    <AppLayoutSidebarLaunched
      {...{
        status,
        analysis,
        analysisRequired,
        analysisError,
        experiment,
        refetch,
      }}
    >
      {children}
    </AppLayoutSidebarLaunched>
  ) : (
    <AppLayoutWithSidebar {...{ experiment, refetch }}>
      {children}
    </AppLayoutWithSidebar>
  );

export default AppLayoutWithExperiment;
