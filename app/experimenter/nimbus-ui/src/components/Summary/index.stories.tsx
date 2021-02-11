/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import { storiesOf } from "@storybook/react";
import React from "react";
import Summary from ".";
import { END_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { mockExperimentMutation, mockExperimentQuery } from "../../lib/mocks";
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
  .add("live status", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
    });
    const mutationMock = mockExperimentMutation(
      END_EXPERIMENT_MUTATION,
      {
        id: experiment.id!,
      },
      "endExperiment",
    );
    return <Subject {...{ experiment, mocks: [mutationMock] }} />;
  })
  .add("end requested", () => {
    const { experiment } = mockExperimentQuery("demo-slug", {
      status: NimbusExperimentStatus.LIVE,
      isEndRequested: true,
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
  mocks = [],
}: {
  experiment: getExperiment_experimentBySlug;
  mocks?: MockedResponse<Record<string, any>>[];
}) => (
  <AppLayout>
    <RouterSlugProvider {...{ mocks }}>
      <Summary {...{ experiment }} />
    </RouterSlugProvider>
  </AppLayout>
);
