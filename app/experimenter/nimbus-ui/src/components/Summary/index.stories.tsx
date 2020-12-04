/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { mockExperimentQuery } from "../../lib/mocks";
import AppLayout from "../AppLayout";
import Summary from ".";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

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
