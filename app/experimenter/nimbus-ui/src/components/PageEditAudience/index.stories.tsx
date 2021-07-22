/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { withQuery } from "@storybook/addon-queryparams";
import React from "react";
import PageEditAudience from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

export default {
  title: "pages/EditAudience",
  component: PageEditAudience,
  decorators: [withLinks, withQuery],
};

const storyWithExperiment = (
  experiment?: Partial<getExperiment_experimentBySlug>,
) => {
  const { mock } = mockExperimentQuery("demo-slug", experiment);
  return (
    <RouterSlugProvider mocks={[mock]}>
      <PageEditAudience />
    </RouterSlugProvider>
  );
};

export const Basic = () => storyWithExperiment();

export const MissingFields = () =>
  storyWithExperiment({
    readyForReview: {
      ready: false,
      message: {
        population_percent: [
          "When it feels like the world is on your shoulders",
        ],
        proposed_duration: ["And all the madness has got you goin' crazy"],
        proposed_enrollment: ["It's time to get out"],
        total_enrolled_clients: ["Step out into the street"],
        firefox_min_version: [
          "Where all of the action is right there at your feet.",
        ],
        targeting_config_slug: [
          "Well, I know a place",
          "Where we can dance the whole night away",
        ],
        countries: ["Just come with me"],
        locales: ["We can shake it loose right away"],
      },
    },
  });
MissingFields.parameters = {
  query: {
    "show-errors": true,
  },
};
