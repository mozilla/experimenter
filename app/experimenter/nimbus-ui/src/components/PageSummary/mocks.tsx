/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import PageSummary from ".";
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

export function createFullStatusMutationMock(
  id: number,
  status = NimbusExperimentStatus.DRAFT,
  statusNext = null as NimbusExperimentStatus | null,
  publishStatus = NimbusExperimentPublishStatus.IDLE,
  changelogMessage?: string,
) {
  return mockExperimentMutation(
    UPDATE_EXPERIMENT_MUTATION,
    { id, publishStatus, statusNext, status, changelogMessage },
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
      <PageSummary polling={false} />
    </RouterSlugProvider>
  );
};

export const reviewRequestedBaseProps = {
  status: NimbusExperimentStatus.DRAFT,
  statusNext: NimbusExperimentStatus.LIVE,
  publishStatus: NimbusExperimentPublishStatus.REVIEW,
  reviewRequest: mockChangelog(),
};

export const reviewPendingBaseProps = {
  status: NimbusExperimentStatus.DRAFT,
  statusNext: NimbusExperimentStatus.LIVE,
  publishStatus: NimbusExperimentPublishStatus.WAITING,
  reviewRequest: mockChangelog(),
};

export const reviewTimedoutBaseProps = {
  status: NimbusExperimentStatus.DRAFT,
  statusNext: NimbusExperimentStatus.LIVE,
  publishStatus: NimbusExperimentPublishStatus.REVIEW,
  reviewRequest: mockChangelog(),
  timeout: mockChangelog("def@mozilla.com"),
};

export const reviewRejectedBaseProps = {
  status: NimbusExperimentStatus.DRAFT,
  statusNext: null,
  publishStatus: NimbusExperimentPublishStatus.IDLE,
  reviewRequest: mockChangelog(),
  rejection: mockChangelog("def@mozilla.com", "It's bad. Just start over."),
};

export const endReviewRequestedBaseProps = {
  status: NimbusExperimentStatus.LIVE,
  statusNext: NimbusExperimentStatus.COMPLETE,
  publishStatus: NimbusExperimentPublishStatus.REVIEW,
  reviewRequest: mockChangelog(),
};
