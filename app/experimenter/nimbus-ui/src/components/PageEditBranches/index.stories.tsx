/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { withQuery } from "@storybook/addon-queryparams";
import React from "react";
import PageEditBranches from ".";
import { SERVER_ERRORS } from "../../lib/constants";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { NimbusExperimentApplicationEnum } from "../../types/globalTypes";

const featureConfigs = [
  {
    id: 2,
    name: "Mauris odio erat",
    slug: "mauris-odio-erat",
    description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    application: NimbusExperimentApplicationEnum.FENIX,
    ownerEmail: "dude23@yahoo.com",
    schema: '{ "sample": "schema" }',
  },
];

const emptyBranches: Partial<getExperiment_experimentBySlug> = {
  referenceBranch: {
    id: null,
    name: "",
    slug: "",
    description: "",
    ratio: 1,
    featureValue: "",
    featureEnabled: false,
    screenshots: [],
  },
  treatmentBranches: [
    {
      id: null,
      name: "",
      slug: "",
      description: "",
      ratio: 1,
      featureValue: "woop woop",
      featureEnabled: true,
      screenshots: [],
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

export const FilledOutFields = () => storyWithExperiment({ featureConfigs });

export const MissingFields = () =>
  storyWithExperiment({
    featureConfigs,
    ...emptyBranches,
    readyForReview: {
      ready: false,
      message: {
        feature_config: [SERVER_ERRORS.FEATURE_CONFIG],
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
          },
        ],
      },
      warnings: {
        treatment_branches: [
          {
            feature_value: ["Sugar we're going down swinging"],
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
