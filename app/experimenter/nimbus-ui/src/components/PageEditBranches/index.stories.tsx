/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { withLinks } from "@storybook/addon-links";
import { withQuery } from "@storybook/addon-queryparams";
import { storiesOf } from "@storybook/react";
import React from "react";
import PageEditBranches from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";
import { NimbusFeatureConfigApplication } from "../../types/globalTypes";

const { mock } = mockExperimentQuery("demo-slug", {
  featureConfig: {
    __typename: "NimbusFeatureConfigType",
    id: "2",
    name: "Mauris odio erat",
    slug: "mauris-odio-erat",
    description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    application: NimbusFeatureConfigApplication.FENIX,
    ownerEmail: "dude23@yahoo.com",
    schema: '{ "sample": "schema" }',
  },
});

const { mock: mockMissingFields } = mockExperimentQuery("demo-slug", {
  referenceBranch: {
    __typename: "NimbusBranchType",
    name: "",
    slug: "",
    description: "",
    ratio: 1,
    featureValue: "",
    featureEnabled: false,
  },
  treatmentBranches: [
    {
      __typename: "NimbusBranchType",
      name: "",
      slug: "",
      description: "",
      ratio: 1,
      featureValue: "",
      featureEnabled: false,
    },
  ],
  readyForReview: {
    __typename: "NimbusReadyForReviewType",
    ready: false,
    message: {
      reference_branch: ["This field may not be null."],
    },
  },
});

storiesOf("pages/EditBranches", module)
  .addDecorator(withLinks)
  .addDecorator(withQuery)
  .add("basic", () => (
    <RouterSlugProvider mocks={[mock]}>
      <PageEditBranches />
    </RouterSlugProvider>
  ))
  .add(
    "missing fields",
    () => (
      <RouterSlugProvider mocks={[mockMissingFields]}>
        <PageEditBranches />
      </RouterSlugProvider>
    ),
    {
      query: {
        "show-errors": true,
      },
    },
  );
