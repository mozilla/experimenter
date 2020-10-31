/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps, useParams } from "@reach/router";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import { useExperiment, useConfig } from "../../hooks";
import HeaderEditExperiment from "../HeaderEditExperiment";
import ExperimentNotFound from "../PageExperimentNotFound";
import PageLoading from "../PageLoading";
import FormBranches from "../FormBranches";
import LinkExternal from "../LinkExternal";

// TODO: find this doco URL
const BRANCHES_DOC_URL =
  "https://mana.mozilla.org/wiki/pages/viewpage.action?spaceKey=FJT&title=Project+Nimbus";

const PageEditBranches: React.FunctionComponent<RouteComponentProps> = () => {
  const { slug } = useParams();
  const { experiment, notFound, loading } = useExperiment(slug);
  const { featureConfig } = useConfig();

  if (loading) {
    return <PageLoading />;
  }

  if (notFound) {
    return <ExperimentNotFound {...{ slug }} />;
  }

  const { name, status } = experiment;
  return (
    <AppLayoutWithSidebar>
      <section data-testid="PageEditBranches">
        <HeaderEditExperiment
          {...{
            slug,
            name,
            status,
          }}
        />
        <h2 className="mt-3 h4">Branches</h2>
        <p>
          If you want, you can add a <strong>feature flag</strong> configuration
          to each branch. Experiments can only change one flag at a time.{" "}
          <LinkExternal href={BRANCHES_DOC_URL}>Learn more</LinkExternal>
        </p>
        {/* TODO: EXP-505 for accepting and saving edits to branches */}
        <FormBranches
          {...{
            experiment,
            featureConfig,
            // TODO: supply this as default value, track changes within FormBranches
            equalRatio: false,
          }}
        />
      </section>
    </AppLayoutWithSidebar>
  );
};

export default PageEditBranches;
