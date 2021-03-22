/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import PageRequestReview from ".";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { MockConfigContext } from "../../hooks";
import { mockExperimentMutation, mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import DraftStatusOperations from "./DraftStatusOperations";

export const { mock, experiment } = mockExperimentQuery("demo-slug");

export function createMutationMock(
  id: number,
  status = NimbusExperimentStatus.REVIEW,
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

export const Subject = ({
  mocks = [mock, createMutationMock(experiment.id!)],
}: {
  mocks?: React.ComponentProps<typeof RouterSlugProvider>["mocks"];
}) => (
  <RouterSlugProvider {...{ mocks }}>
    <PageRequestReview polling={false} />
  </RouterSlugProvider>
);

export const SubjectEXP1055 = ({
  mocks = [mock, createMutationMock(experiment.id!)],
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

export const SubjectDraftStatusOperations = ({
  isLaunchRequested = false,
  isLaunchApproved = false,
  launchRequestedByUsername = "jdoe@mozilla.com",
  currentUsername = "janed@mozilla.com",
  currentUserCanApprove = false,
  rejectFeedback = null,
  rejectExperimentLaunch = () => {},
  approveExperimentLaunch = () => {},
  confirmExperimentLaunchApproval = () => {},
  onLaunchClicked = () => {},
  onLaunchToPreviewClicked = () => {},
  ...props
}: Partial<React.ComponentProps<typeof DraftStatusOperations>>) => (
  <DraftStatusOperations
    {...{
      featureFlags: {
        exp1055ReviewFlow: true,
      },
      isLoading: false,
      isLaunchRequested,
      isLaunchApproved,
      currentUserCanApprove,
      currentUsername,
      launchRequestedByUsername,
      rejectExperimentLaunch,
      rejectFeedback,
      approveExperimentLaunch,
      confirmExperimentLaunchApproval,
      onLaunchClicked,
      onLaunchToPreviewClicked,
      ...props,
    }}
  />
);
