/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import { RouteComponentProps, useParams } from "@reach/router";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import { useExperiment } from "../../hooks";
import HeaderEditExperiment from "../HeaderEditExperiment";
import PageExperimentNotFound from "../PageExperimentNotFound";
import PageLoading from "../PageLoading";
import FormOverview from "../FormOverview";

type PageEditOverviewProps = {} & RouteComponentProps;

const PageEditOverview: React.FunctionComponent<PageEditOverviewProps> = () => {
  // TODO: EXP-462 Get this from constants / config loaded at app start?
  const applications = ["firefox-desktop", "fenix", "reference-browser"];

  const { slug } = useParams();
  const { experiment, notFound, loading } = useExperiment(slug);
  const [submitErrors /* setSubmitErrors */] = useState<Record<string, any>>(
    {},
  );

  const onFormSubmit = useCallback(() => {
    console.log("SUBMIT TBD");
  }, []);

  const onFormNext = useCallback(() => {
    console.log("NEXT TBD");
  }, []);

  if (loading) {
    return <PageLoading />;
  }

  if (notFound) {
    return <PageExperimentNotFound {...{ slug }} />;
  }

  const { name, status } = experiment;

  return (
    <AppLayoutWithSidebar>
      <section data-testid="PageEditOverview">
        <HeaderEditExperiment
          {...{
            slug,
            name,
            status,
          }}
        />
        <h2 className="mt-3 mb-4 h4">Overview</h2>
        <FormOverview
          {...{
            isLoading: loading,
            applications,
            experiment,
            submitErrors,
            onSubmit: onFormSubmit,
            onNext: onFormNext,
          }}
        />
      </section>
    </AppLayoutWithSidebar>
  );
};

export default PageEditOverview;
