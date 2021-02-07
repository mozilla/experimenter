/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import Summary from ".";
import { MockExperimentContextProvider } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment } from "../../types/getExperiment";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import AppLayout from "../AppLayout";

storiesOf("components/Summary", module)
  .add("draft status", () => <Subject />)
  .add("non-draft status", () => (
    <Subject experiment={{ status: NimbusExperimentStatus.ACCEPTED }} />
  ))
  .add("no branches", () => (
    <Subject
      experiment={{
        referenceBranch: null,
        treatmentBranches: null,
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
        <Summary />
      </RouterSlugProvider>
    </AppLayout>
  </MockExperimentContextProvider>
);
