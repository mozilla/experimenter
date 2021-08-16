/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import React from "react";
import SidebarActions from ".";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { Subject } from "./mocks";

export default {
  title: "components/SidebarActions",
  component: SidebarActions,
  decorators: [withLinks],
};

const storyWithExperimentProps = (
  props: Partial<getExperiment_experimentBySlug>,
  storyName?: string,
) => {
  const story = () => <Subject experiment={props} />;
  story.storyName = storyName;
  return story;
};

export const ArchiveDisabled = storyWithExperimentProps(
  {
    canArchive: false,
  },
  "Archiving disabled",
);

export const ArchiveEnabled = storyWithExperimentProps(
  {
    canArchive: true,
  },
  "Archiving enabled",
);
