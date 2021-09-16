/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { MockedResponse } from "@apollo/client/testing";
import React from "react";
import Summary from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import {
  mockChangelog,
  mockExperimentMutation,
  mockExperimentQuery,
} from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../types/globalTypes";
import AppLayout from "../AppLayout";

export function createMutationMock(
  id: number,
  publishStatus: NimbusExperimentPublishStatus,
  additionalProps: Record<string, any> = {},
) {
  return mockExperimentMutation(
    UPDATE_EXPERIMENT_MUTATION,
    {
      id,
      publishStatus,
      ...additionalProps,
    },
    "updateExperiment",
    {
      experiment: {
        publishStatus,
        ...additionalProps,
      },
    },
  );
}

export const Subject = ({
  props = {},
  mocks = [],
  refetch = () => Promise.resolve(),
}: {
  props?: Partial<getExperiment_experimentBySlug | null>;
  mocks?: MockedResponse<Record<string, any>>[];
  refetch?: () => Promise<unknown>;
}) => {
  const { experiment, mock } = mockExperimentQuery("demo-slug", props);

  return (
    <AppLayout>
      <RouterSlugProvider mocks={[mock, ...mocks]}>
        <Summary {...{ experiment, refetch }} />
      </RouterSlugProvider>
    </AppLayout>
  );
};

export const reviewRequestedBaseProps = {
  status: NimbusExperimentStatus.LIVE,
  statusNext: NimbusExperimentStatus.COMPLETE,
  publishStatus: NimbusExperimentPublishStatus.REVIEW,
  canReview: false,
  reviewRequest: mockChangelog(),
};

export const reviewPendingBaseProps = {
  status: NimbusExperimentStatus.LIVE,
  statusNext: NimbusExperimentStatus.COMPLETE,
  publishStatus: NimbusExperimentPublishStatus.WAITING,
  reviewRequest: mockChangelog(),
};

export const reviewTimedoutBaseProps = {
  status: NimbusExperimentStatus.LIVE,
  statusNext: NimbusExperimentStatus.COMPLETE,
  publishStatus: NimbusExperimentPublishStatus.REVIEW,
  reviewRequest: mockChangelog(),
  timeout: mockChangelog("def@mozilla.com"),
};

export const reviewRejectedBaseProps = {
  status: NimbusExperimentStatus.LIVE,
  statusNext: null,
  publishStatus: NimbusExperimentPublishStatus.IDLE,
  reviewRequest: mockChangelog(),
  rejection: mockChangelog("def@mozilla.com", "It's bad. Just start over."),
};

export const MOCK_SCREENSHOTS = [
  {
    id: 123,
    description: "Meow meow.",
    image: "https://placekitten.com/240/240",
  },
  {
    id: 456,
    description: "Foo bar baz.",
    image: "https://via.placeholder.com/320x240.png?text=Screenshot",
  },
  {
    id: 789,
    description: "Meow meow.",
    image: "https://placekitten.com/1280/720",
  },
  {
    id: 321,
    description: "Foo bar baz.",
    image: "https://via.placeholder.com/800x600.png?text=Screenshot",
  },
];
