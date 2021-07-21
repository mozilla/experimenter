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

export default {
  title: "pages/Home/DirectoryTable",
  component: DirectoryTable,
  decorators: [withLinks],
};

export const Basic = () => (
  <DirectoryTable experiments={mockDirectoryExperiments()} />
);

export const Live = () => (
  <DirectoryLiveTable experiments={mockDirectoryExperiments()} />
);

export const Completed = () => (
  <DirectoryCompleteTable experiments={mockDirectoryExperiments()} />
);

export const Drafts = () => (
  <DirectoryDraftsTable experiments={mockDirectoryExperiments()} />
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
