/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import React from "react";
import ArchiveDialogue from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { CHANGELOG_MESSAGES } from "../../lib/constants";
import {
  MockedCache,
  mockExperimentMutation,
  mockExperimentQuery,
} from "../../lib/mocks";

export const Subject = ({
  mocks,
  experimentId,
  refetch = () => Promise.resolve(),
  onClose = () => {},
}: Partial<React.ComponentProps<typeof ArchiveDialogue>> & {
  experimentId?: number;
  mocks?: MockedResponse[];
}) => {
  const { mock: queryMock, experiment } = mockExperimentQuery();
  const mutationMock = mockExperimentMutation(
    UPDATE_EXPERIMENT_MUTATION,
    {
      id: experiment.id,
      changelogMessage: CHANGELOG_MESSAGES.ARCHIVING_EXPERIMENT,
      isArchived: true,
      archiveReason: "foo",
    },
    "updateExperiment",
  );

  return (
    <MockedCache mocks={mocks || [queryMock, mutationMock]}>
      <>
        <p>Type &quot;foo&quot;</p>
        <ArchiveDialogue
          {...{
            onClose,
            refetch,
            experimentId: experimentId || experiment.id!,
          }}
        />
      </>
    </MockedCache>
  );
};
