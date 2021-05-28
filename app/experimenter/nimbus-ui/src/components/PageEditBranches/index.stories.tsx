/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { withQuery } from "@storybook/addon-queryparams";
import React from "react";
import PageEditBranches from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { NimbusExperimentApplication } from "../../types/globalTypes";

const featureConfig = {
  id: 2,
  name: "Mauris odio erat",
  slug: "mauris-odio-erat",
  description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
  application: NimbusExperimentApplication.FENIX,
  ownerEmail: "dude23@yahoo.com",
  schema: '{ "sample": "schema" }',
};

const emptyBranches = {
  referenceBranch: {
    name: "",
    slug: "",
    description: "",
    ratio: 1,
    featureValue: "",
    featureEnabled: false,
  },
  treatmentBranches: [
    {
      name: "",
      slug: "",
      description: "",
      ratio: 1,
      featureValue: "woop woop",
      featureEnabled: true,
    },
  ],
};

export default {
  title: "pages/EditBranches",
  component: PageEditBranches,
  decorators: [withLinks, withQuery],
};

const storyWithExperiment = (
  experiment?: Partial<getExperiment_experimentBySlug>,
) => {
  const { mock } = mockExperimentQuery("demo-slug", experiment);
  return (
    <RouterSlugProvider mocks={[mock]}>
      <PageEditBranches />
    </RouterSlugProvider>
  );
};

export const Basic = () => storyWithExperiment(emptyBranches);

export const FilledOutFields = () => storyWithExperiment({ featureConfig });

export const MissingFields = () =>
  storyWithExperiment({
    featureConfig,
    ...emptyBranches,
    readyForReview: {
      ready: false,
      message: {
        reference_branch: {
          name: ["Drop a heart", "and break a name"],
          description: [
            "We're always sleeping in and sleeping",
            "For the wrong team",
          ],
        },
        treatment_branches: [
          {
            name: ["We're going down"],
            description: ["Down in an earlier round"],
            featureValue: ["Sugar we're going down swinging"],
          },
        ],
      },
    },
  });
MissingFields.parameters = {
  query: {
    "show-errors": true,
  },
};
