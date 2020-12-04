/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { mockExperimentQuery } from "../../lib/mocks";
import AppLayout from "../AppLayout";
import TableAudience from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentChannel } from "../../types/globalTypes";

storiesOf("components/TableAudience", module)
  .add("all fields filled out", () => {
    const { data } = mockExperimentQuery("demo-slug", {
      channels: [NimbusExperimentChannel.DESKTOP_BETA],
    });
    return (
      <Subject>
        <TableAudience experiment={data!} />
      </Subject>
    );
  })
  .add("filled out with multiple channels", () => {
    const { data } = mockExperimentQuery("demo-slug");
    return (
      <Subject>
        <TableAudience experiment={data!} />
      </Subject>
    );
  })
  .add("only required fields filled out", () => {
    const { data } = mockExperimentQuery("demo-slug", {
      totalEnrolledClients: 0,
      targetingConfigSlug: null,
    });
    return (
      <Subject>
        <TableAudience experiment={data!} />
      </Subject>
    );
  })
  .add("missing required fields", () => {
    const { data } = mockExperimentQuery("demo-slug", {
      channels: [],
      firefoxMinVersion: null,
      populationPercent: 0,
      totalEnrolledClients: 0,
      targetingConfigSlug: null,
    });

    return (
      <Subject>
        <TableAudience experiment={data!} />
      </Subject>
    );
  });

const Subject = ({ children }: { children: React.ReactElement }) => (
  <AppLayout>
    <RouterSlugProvider>{children}</RouterSlugProvider>
  </AppLayout>
);
