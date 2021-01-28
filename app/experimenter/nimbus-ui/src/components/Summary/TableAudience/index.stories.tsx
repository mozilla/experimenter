/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import TableAudience from ".";
import { mockExperimentQuery } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { NimbusExperimentChannel } from "../../../types/globalTypes";
import AppLayout from "../../AppLayout";

storiesOf("components/Summary/TableAudience", module)
  .add("all fields filled out", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      channel: NimbusExperimentChannel.BETA,
    });
    return (
      <Subject>
        <TableAudience {...{ experiment }} />
      </Subject>
    );
  })
  .add("only required fields filled out", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      totalEnrolledClients: 0,
      targetingConfigSlug: null,
    });
    return (
      <Subject>
        <TableAudience {...{ experiment }} />
      </Subject>
    );
  })
  .add("missing required fields", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      channel: null,
      firefoxMinVersion: null,
      populationPercent: "0",
      totalEnrolledClients: 0,
      targetingConfigSlug: null,
    });

    return (
      <Subject>
        <TableAudience {...{ experiment }} />
      </Subject>
    );
  });

const Subject = ({ children }: { children: React.ReactElement }) => (
  <AppLayout>
    <RouterSlugProvider>{children}</RouterSlugProvider>
  </AppLayout>
);
