/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import AppLayoutWithSidebar from ".";
import { NimbusExperimentStatus } from "../../types/globalTypes";
import { Subject } from "./mocks";

export default {
  title: "components/AppLayoutWithSidebar",
  component: AppLayoutWithSidebar,
  decorators: [withLinks],
};

export const DraftStatus = () => (
  <Subject
    experiment={{
      status: NimbusExperimentStatus.DRAFT,
    }}
  />
);

export const PreviewStatus = () => (
  <Subject
    experiment={{
      status: NimbusExperimentStatus.PREVIEW,
    }}
  />
);

export const MissingDetails = () => (
  <Subject
    experiment={{
      readyForReview: {
        ready: false,
        message: {
          reference_branch: ["This field may not be null."],
          channel: ["This list may not be empty."],
        },
      },
    }}
  />
);
