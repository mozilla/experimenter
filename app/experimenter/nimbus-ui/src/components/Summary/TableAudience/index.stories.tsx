/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import TableAudience from ".";
import { MockExperimentContextProvider } from "../../../lib/mocks";
import { RouterSlugProvider } from "../../../lib/test-utils";
import { getExperiment } from "../../../types/getExperiment";
import { NimbusExperimentChannel } from "../../../types/globalTypes";
import AppLayout from "../../AppLayout";

storiesOf("components/Summary/TableAudience", module)
  .add("all fields filled out", () => (
    <Subject
      experiment={{
        channel: NimbusExperimentChannel.BETA,
      }}
    />
  ))
  .add("only required fields filled out", () => (
    <Subject
      experiment={{
        totalEnrolledClients: 0,
        targetingConfigSlug: null,
      }}
    />
  ))
  .add("missing required fields", () => (
    <Subject
      experiment={{
        channel: null,
        firefoxMinVersion: null,
        populationPercent: "0",
        totalEnrolledClients: 0,
        targetingConfigSlug: null,
      }}
    />
  ));

const Subject = ({
  experiment: overrides = {},
}: {
  experiment?: Partial<getExperiment["experimentBySlug"]>;
}) => (
  <MockExperimentContextProvider {...{ overrides }}>
    <AppLayout>
      <RouterSlugProvider>
        <TableAudience />
      </RouterSlugProvider>
    </AppLayout>
  </MockExperimentContextProvider>
);
