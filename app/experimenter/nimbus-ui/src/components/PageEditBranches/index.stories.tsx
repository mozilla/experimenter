/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { RouterSlugProvider } from "../../lib/test-utils";
import { withLinks } from "@storybook/addon-links";
import { withQuery } from "@storybook/addon-queryparams";
import { mockExperimentQuery } from "../../lib/mocks";
import PageEditBranches from ".";

const { mock } = mockExperimentQuery("demo-slug");
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
