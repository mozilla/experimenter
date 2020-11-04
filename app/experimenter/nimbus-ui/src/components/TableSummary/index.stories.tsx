/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { mockExperimentQuery } from "../../lib/mocks";
import AppLayout from "../AppLayout";
import TableSummary from ".";
import { RouterSlugProvider } from "../../lib/test-utils";

storiesOf("components/TableSummary", module)
  .add("filled out", () => {
    const { data } = mockExperimentQuery("demo-slug");
    return (
      <Subject>
        <TableSummary experiment={data!} />
      </Subject>
    );
  })
  .add("partially filled out", () => {
    const { data } = mockExperimentQuery("demo-slug", {
      secondaryProbeSets: [],
      channels: [],
      proposedDuration: 0,
    });
    return (
      <Subject>
        <TableSummary experiment={data!} />
      </Subject>
    );
  })
  .add("missing all fields", () => {
    const { data } = mockExperimentQuery("demo-slug", {
      owner: null,
      hypothesis: null,
      primaryProbeSets: [],
      secondaryProbeSets: [],
      channels: [],
      firefoxMinVersion: null,
      populationPercent: 0,
      totalEnrolledClients: 0,
      proposedEnrollment: 0,
      proposedDuration: 0,
      targetingConfigSlug: null,
    });

    return (
      <Subject>
        <TableSummary experiment={data!} />
      </Subject>
    );
  });

const Subject = ({ children }: { children: React.ReactElement }) => (
  <AppLayout>
    <RouterSlugProvider>{children}</RouterSlugProvider>
  </AppLayout>
);
