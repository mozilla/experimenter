/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { UPDATE_EXPERIMENT_STATUS_MUTATION } from "../../gql/experiments";
import { mockExperimentMutation } from "../../lib/mocks";
import { NimbusExperimentStatus } from "../../types/globalTypes";

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
