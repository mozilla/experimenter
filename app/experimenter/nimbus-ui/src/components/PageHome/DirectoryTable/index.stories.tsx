/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import DirectoryTable, {
  DirectoryCompleteTable,
  DirectoryDraftsTable,
  DirectoryLiveTable,
} from ".";
import { mockDirectoryExperiments } from "../../../lib/mocks";
import {
  NimbusExperimentPublishStatus,
  NimbusExperimentStatus,
} from "../../../types/globalTypes";

export default {
  title: "pages/Home/DirectoryTable",
  component: DirectoryTable,
  decorators: [withLinks],
};

const experiments = mockDirectoryExperiments();
const draftExperiments = experiments.filter(
  ({ status, publishStatus }) =>
    status === NimbusExperimentStatus.DRAFT &&
    publishStatus === NimbusExperimentPublishStatus.IDLE,
);
const liveExperiments = experiments.filter(
  ({ status, publishStatus }) =>
    status === NimbusExperimentStatus.LIVE &&
    publishStatus === NimbusExperimentPublishStatus.IDLE,
);
const completedExperiments = experiments.filter(
  ({ status, publishStatus }) =>
    status === NimbusExperimentStatus.COMPLETE &&
    publishStatus === NimbusExperimentPublishStatus.IDLE,
);

export const Basic = () => <DirectoryTable experiments={experiments} />;

export const Live = () => <DirectoryLiveTable experiments={liveExperiments} />;

export const Completed = () => (
  <DirectoryCompleteTable experiments={completedExperiments} />
);

export const Drafts = () => (
  <DirectoryDraftsTable experiments={draftExperiments} />
);

export const CustomComponent = () => (
  <DirectoryTable
    experiments={mockDirectoryExperiments()}
    columns={[
      {
        label: "Testing column",
        component: ({ status }) => <td>Hello {status}</td>,
      },
    ]}
  />
);

export const NoFeature = () => (
  <DirectoryTable
    experiments={mockDirectoryExperiments([{ featureConfig: null }])}
  />
);
