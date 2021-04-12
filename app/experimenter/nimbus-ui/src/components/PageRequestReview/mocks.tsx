/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import PageRequestReview from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { MockConfigContext } from "../../hooks";
import { mockExperimentMutation, mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";

export const { mock, experiment } = mockExperimentQuery("demo-slug");

export function createStatusMutationMock(
  id: number,
  status = NimbusExperimentStatus.DRAFT,
) {
  return mockExperimentMutation(
    UPDATE_EXPERIMENT_MUTATION,
    {
      id,
      status,
    },
    "updateExperiment",
    {
      experiment: {
        status,
      },
    },
  );
}

export function createPublishStatusMutationMock(
  id: number,
  publishStatus = NimbusExperimentPublishStatus.APPROVED,
) {
  return mockExperimentMutation(
    UPDATE_EXPERIMENT_MUTATION,
    {
      id,
      publishStatus,
      status: NimbusExperimentStatus.DRAFT,
    },
    "updateExperiment",
    {
      experiment: {
        publishStatus,
        status: NimbusExperimentStatus.DRAFT,
      },
    },
  );
}

export const Subject = ({
  mocks = [mock, createStatusMutationMock(experiment.id!)],
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
}) => (
  <RouterSlugProvider {...{ mocks }}>
    <PageRequestReview polling={false} />
  </RouterSlugProvider>
);

export const SubjectEXP1143 = ({
  mocks = [mock, createStatusMutationMock(experiment.id!)],
  ...pageProps
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
} & React.ComponentProps<typeof PageRequestReview>) => (
  <MockConfigContext.Provider
    value={{
      featureFlags: {
        exp1055ReviewFlow: true,
      },
    }}
  >
    <RouterSlugProvider {...{ mocks }}>
      <PageRequestReview polling={false} {...pageProps} />
    </RouterSlugProvider>
  </MockConfigContext.Provider>
);
