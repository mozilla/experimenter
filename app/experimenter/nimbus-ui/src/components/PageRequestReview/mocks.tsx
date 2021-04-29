/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import PageRequestReview from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { CHANGELOG_MESSAGES } from "../../lib/constants";
import {
  mockChangelog,
  mockExperimentMutation,
  mockExperimentQuery,
} from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";

export const { mock, experiment } = mockExperimentQuery("demo-slug");

export function createStatusMutationMock(
  id: number,
  status = NimbusExperimentStatus.DRAFT,
  changelogMessage = CHANGELOG_MESSAGES.RETURNED_TO_DRAFT as string,
) {
  return mockExperimentMutation(
    UPDATE_EXPERIMENT_MUTATION,
    {
      id,
      status,
      changelogMessage,
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
  changelogMessage = CHANGELOG_MESSAGES.REVIEW_APPROVED as string,
) {
  return mockExperimentMutation(
    UPDATE_EXPERIMENT_MUTATION,
    {
      id,
      publishStatus,
      status: NimbusExperimentStatus.DRAFT,
      changelogMessage,
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

export function createFullStatusMutationMock(
  id: number,
  status = NimbusExperimentStatus.DRAFT,
  publishStatus = NimbusExperimentPublishStatus.IDLE,
  changelogMessage?: string,
) {
  return mockExperimentMutation(
    UPDATE_EXPERIMENT_MUTATION,
    { id, publishStatus, status, changelogMessage },
    "updateExperiment",
    { experiment: { publishStatus, status } },
  );
}

export const Subject = ({
  mocks = [mock, createStatusMutationMock(experiment.id!)],
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
}) => {
  return (
    <RouterSlugProvider {...{ mocks }}>
      <PageRequestReview polling={false} />
    </RouterSlugProvider>
  );
};

export const reviewRequestedBaseProps = {
  status: NimbusExperimentStatus.DRAFT,
  publishStatus: NimbusExperimentPublishStatus.REVIEW,
  reviewRequest: mockChangelog(),
};

export const reviewPendingBaseProps = {
  status: NimbusExperimentStatus.DRAFT,
  publishStatus: NimbusExperimentPublishStatus.WAITING,
  reviewRequest: mockChangelog(),
};

export const reviewTimedoutBaseProps = {
  status: NimbusExperimentStatus.DRAFT,
  publishStatus: NimbusExperimentPublishStatus.REVIEW,
  reviewRequest: mockChangelog(),
  timeout: mockChangelog("def@mozilla.com"),
};

export const reviewRejectedBaseProps = {
  status: NimbusExperimentStatus.DRAFT,
  publishStatus: NimbusExperimentPublishStatus.IDLE,
  reviewRequest: mockChangelog(),
  rejection: mockChangelog("def@mozilla.com", "It's bad. Just start over."),
};
