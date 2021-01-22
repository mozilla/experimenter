/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import Summary from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import AppLayout from "../AppLayout";

storiesOf("components/Summary", module)
  .add("draft status", () => {
    const { experiment } = mockExperimentQuery("demo-slug");
    return <Subject {...{ experiment }} />;
  })
  .add("non-draft status", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.ACCEPTED,
    });
    return <Subject {...{ experiment }} />;
  })
  .add("no branches", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      referenceBranch: null,
      treatmentBranches: null,
    });
    return <Subject {...{ experiment }} />;
  });

const Subject = ({
  experiment,
}: {
  experiment: getExperiment_experimentBySlug;
}) => (
  <AppLayout>
    <RouterSlugProvider>
      <Summary {...{ experiment }} />
    </RouterSlugProvider>
  </AppLayout>
);
