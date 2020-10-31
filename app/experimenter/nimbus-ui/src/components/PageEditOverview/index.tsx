/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import { RouteComponentProps } from "@reach/router";
import FormOverview from "../FormOverview";
import PageEditContainer from "../PageEditContainer";

type PageEditOverviewProps = {} & RouteComponentProps;

const PageEditOverview: React.FunctionComponent<PageEditOverviewProps> = () => {
  // TODO: EXP-462 Get this from constants / config loaded at app start?
  const applications = ["firefox-desktop", "fenix", "reference-browser"];

  const [submitErrors /* setSubmitErrors */] = useState<Record<string, any>>(
    {},
  );

  const onFormSubmit = useCallback(() => {
    console.log("SUBMIT TBD");
  }, []);

  const onFormNext = useCallback(() => {
    console.log("NEXT TBD");
  }, []);

  return (
    <PageEditContainer title="Overview" testId="PageEditOverview">
      {({ experiment }) => (
        <FormOverview
          {...{
            isLoading: false,
            applications,
            experiment,
            submitErrors,
            onSubmit: onFormSubmit,
            onNext: onFormNext,
          }}
        />
      )}
    </PageEditContainer>
  );
};

export default PageEditOverview;
