/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import FormBranches, { FormBranch } from ".";
import { mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";

export const SubjectBranch = ({
  branch = MOCK_BRANCH,
  equalRatio = false,
  isReference = false,
  experimentFeatureConfig = MOCK_FEATURE_CONFIG,
  featureConfig = MOCK_CONFIG.featureConfig,
}: Partial<React.ComponentProps<typeof FormBranch>>) => (
  <div className="p-5">
    <FormBranch
      {...{
        branch,
        isReference,
        equalRatio,
        featureConfig,
        experimentFeatureConfig,
      }}
    />
  </div>
);

export const SubjectBranches = ({
  experiment = MOCK_EXPERIMENT,
  equalRatio = false,
  featureConfig = MOCK_CONFIG.featureConfig,
}: Partial<React.ComponentProps<typeof FormBranches>> = {}) => (
  <div className="p-5">
    <FormBranches
      {...{
        experiment,
        equalRatio,
        featureConfig,
      }}
    />
  </div>
);

export const MOCK_EXPERIMENT = mockExperimentQuery("demo-slug", {
  treatmentBranches: [
    {
      __typename: "NimbusBranchType",
      name: "Managed zero tolerance projection",
      slug: "managed-zero-tolerance-projection",
      description: "Next ask then he in degree order.",
      ratio: 1,
      featureValue: '{"effect-effect-whole": "close-teach-exactly"}',
      featureEnabled: false,
    },
    {
      __typename: "NimbusBranchType",
      name: "Salt way link",
      slug: "salt-way-link",
      description: "Flame the dark true.",
      ratio: 1,
      featureValue: '{"frosted-wake": "simple-hesitation"}',
      featureEnabled: true,
    },
  ],
})!.data!;

export const MOCK_BRANCH = MOCK_EXPERIMENT.treatmentBranches![0]!;
export const MOCK_FEATURE_CONFIG = MOCK_CONFIG.featureConfig![0]!;
export const MOCK_FEATURE_CONFIG_WITH_SCHEMA = MOCK_CONFIG.featureConfig![1]!;
