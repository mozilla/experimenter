/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RouteComponentProps, useParams } from "@reach/router";
import AppLayoutWithSidebar from "../AppLayoutWithSidebar";
import { useExperiment } from "../../hooks";

type PageEditBranchesProps = {} & RouteComponentProps;

const PageEditBranches = (props: PageEditBranchesProps) => {
  const { slug } = useParams();
  const { experiment } = useExperiment(slug);

  if (experiment != null) {
    console.log(experiment.referenceBranch, experiment.treatmentBranches);
  }

  return (
    <AppLayoutWithSidebar>
      <section data-testid="PageEditBranches">
        <h1>PageEditBranches</h1>
      </section>
    </AppLayoutWithSidebar>
  );
};

export default PageEditBranches;
