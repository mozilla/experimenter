/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import {
  SubjectBranch,
  SubjectBranches,
  MOCK_EXPERIMENT,
  MOCK_BRANCH,
  MOCK_FEATURE_CONFIG,
  MOCK_FEATURE_CONFIG_WITH_SCHEMA,
} from "./mocks";

storiesOf("components/FormBranches/FormBranch", module)
  .add("reference branch", () => (
    <SubjectBranch
      branch={MOCK_EXPERIMENT.referenceBranch!}
      isReference={true}
    />
  ))
  .add("treatment branch", () => <SubjectBranch />)
  .add("equal ratio", () => <SubjectBranch equalRatio />)
  .add("with feature", () => (
    <SubjectBranch
      experimentFeatureConfig={MOCK_FEATURE_CONFIG}
      branch={{
        ...MOCK_BRANCH,
        featureEnabled: false,
        featureValue: "this is a default value",
      }}
    />
  ))
  .add("with feature value", () => (
    <SubjectBranch
      experimentFeatureConfig={MOCK_FEATURE_CONFIG_WITH_SCHEMA}
      branch={{
        ...MOCK_BRANCH,
        featureEnabled: true,
        featureValue: "this is a default value",
      }}
    />
  ));

storiesOf("components/FormBranches", module)
  .add("with branches", () => <SubjectBranches />)
  .add("with equal ratio", () => <SubjectBranches equalRatio={true} />)
  .add("empty", () => (
    <SubjectBranches
      experiment={{
        ...MOCK_EXPERIMENT,
        referenceBranch: null,
        treatmentBranches: null,
      }}
    />
  ))
  .add("with features", () => (
    <SubjectBranches
      experiment={{
        ...MOCK_EXPERIMENT,
        featureConfig: MOCK_FEATURE_CONFIG,
      }}
    />
  ))
  .add("with feature values", () => (
    <SubjectBranches
      experiment={{
        ...MOCK_EXPERIMENT,
        featureConfig: MOCK_FEATURE_CONFIG_WITH_SCHEMA,
      }}
    />
  ));
