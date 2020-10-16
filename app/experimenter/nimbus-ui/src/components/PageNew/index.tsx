/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback } from "react";
import { RouteComponentProps } from "@reach/router";
import AppLayout from "../AppLayout";
import LinkExternal from "../LinkExternal";
import FormExperimentOverviewPartial from "../FormExperimentOverviewPartial";

const TRAINING_DOC_URL =
  "https://mana.mozilla.org/wiki/display/FJT/Project+Nimbus";

type PageNewProps = {} & RouteComponentProps;

const PageNew = (props: PageNewProps) => {
  // TODO: Get this from constants / config loaded at app start?
  const applications = ["firefox-desktop", "fenix", "reference-browser"];

  const onFormSubmit = useCallback((data: Record<string, any>) => {
    console.log("CREATE TBD", data);
  }, []);

  const onFormCancel = useCallback((ev: React.FormEvent) => {
    console.log("CANCEL TBD");
  }, []);

  return (
    <AppLayout testid="PageNew">
      <h1>Create a new Experiment</h1>
      <p>
        Before launching an experiment, review the{" "}
        <LinkExternal href={TRAINING_DOC_URL}>
          training and planning documentation
        </LinkExternal>
        .
      </p>
      <section>
        <FormExperimentOverviewPartial
          {...{ applications, onSubmit: onFormSubmit, onCancel: onFormCancel }}
        />
      </section>
    </AppLayout>
  );
};

export default PageNew;
