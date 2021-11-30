/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { withQuery } from "@storybook/addon-queryparams";
import React from "react";
import PageEditMetrics from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

export default {
  title: "pages/EditMetrics",
  component: PageEditMetrics,
  decorators: [withLinks, withQuery],
};

const storyWithExperiment = (
  experiment?: Partial<getExperiment_experimentBySlug>,
) => {
  const { mock } = mockExperimentQuery("demo-slug", experiment);
  return (
    <RouterSlugProvider mocks={[mock]}>
      <PageEditMetrics />
    </RouterSlugProvider>
  );
};

export const Basic = () => storyWithExperiment();

export const MissingFields = () =>
  storyWithExperiment({
    readyForReview: {
      ready: false,
      message: {
        primary_outcomes: ["Primarily, tell me what's up."],
        secondary_outcomes: ["On second thought..."],
      },
      warnings: {},
    },
  });
MissingFields.parameters = {
  query: {
    "show-errors": true,
  },
};
