/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { withQuery } from "@storybook/addon-queryparams";
import React from "react";
import PageEditOverview from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";

export default {
  title: "pages/EditOverview",
  component: PageEditOverview,
  decorators: [withLinks, withQuery],
};

const storyWithExperiment = (
  experiment?: Partial<getExperiment_experimentBySlug>,
) => {
  const { mock } = mockExperimentQuery("demo-slug", experiment);
  return (
    <RouterSlugProvider mocks={[mock]}>
      <PageEditOverview />
    </RouterSlugProvider>
  );
};

export const Basic = () => storyWithExperiment();

export const MissingFields = () =>
  storyWithExperiment({
    readyForReview: {
      ready: false,
      message: {
        name: ["That's not your real name"],
        hypothesis: ["You really think that's gonna happen?"],
        application: ["Firefox for Palm Trio"],
        public_description: ["Give Carly Rae Jepson a sword"],
        risk_brand: ["Be nice to Foxy!"],
        risk_revenue: ["Racks on racks on racks.", "Yuh, yuh, yuh, let's go"],
        risk_partner_related: ["Be noice to your friends"],
        documentation_links: [
          {
            title: ["Stop being so en-title-d"],
            link: ["Link it up bro"],
          },
        ],
      },
      warnings: {},
    },
  });
MissingFields.parameters = {
  query: {
    "show-errors": true,
  },
};
