/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import EndExperiment from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../../gql/experiments";
import { getStatus } from "../../../lib/experiment";
import {
  MockedCache,
  mockExperimentMutation,
  mockExperimentQuery,
} from "../../../lib/mocks";
import { NimbusExperimentStatus } from "../../../types/globalTypes";

storiesOf("components/Summary/EndExperiment", module)
  .add("status: live", () => <Subject />)
  .add("status: ending", () => <Subject ending />);

const Subject = ({ ending = false }: { ending?: boolean }) => {
  const { experiment } = mockExperimentQuery("demo-slug", {
    status: NimbusExperimentStatus.LIVE,
    isEndRequested: ending,
  });
  const experimentStatus = getStatus(experiment);
  const mutationMock = mockExperimentMutation(
    UPDATE_EXPERIMENT_MUTATION,
    {
      id: experiment.id!,
    },
    "endExperiment",
  );

  return (
    <MockedCache mocks={[mutationMock]}>
      <div className="container-lg py-5">
        <EndExperiment {...{ experiment, status: experimentStatus }} />
      </div>
    </MockedCache>
  );
};
