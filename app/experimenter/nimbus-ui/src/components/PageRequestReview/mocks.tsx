/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import PageRequestReview from ".";
import { UPDATE_EXPERIMENT_STATUS_MUTATION } from "../../gql/experiments";
import { MockConfigContext } from "../../hooks";
import { mockExperimentMutation, mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";

export const { mock, experiment } = mockExperimentQuery("demo-slug");

export function createMutationMock(id: number) {
  return mockExperimentMutation(
    UPDATE_EXPERIMENT_STATUS_MUTATION,
    {
      id,
      status: NimbusExperimentStatus.REVIEW,
    },
    "updateExperiment",
    {
      experiment: {
        status: NimbusExperimentStatus.REVIEW,
      },
    },
  );
}

export const SubjectEXP866 = ({
  mocks = [mock],
  ...pageProps
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
} & Partial<React.ComponentProps<typeof PageRequestReview>>) => (
  <MockConfigContext.Provider value={{ featureFlags: { exp866Preview: true } }}>
    <RouterSlugProvider mocks={mocks}>
      <PageRequestReview
        {...{
          polling: false,
          ...pageProps,
        }}
      />
    </RouterSlugProvider>
  </MockConfigContext.Provider>
);
