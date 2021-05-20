/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import { MOCK_EXPERIMENT, Subject } from "./mocks";

storiesOf("components/Summary/TableBranches", module)
  .add("full branches", () => <Subject />)
  .add("one branch", () => (
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        treatmentBranches: [
          {
            name: "",
            slug: "",
            description: "",
            ratio: 0,
            featureValue: null,
            featureEnabled: false,
          },
        ],
      }}
    />
  ))
  .add("unsaved branches", () => (
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        referenceBranch: {
          ...MOCK_EXPERIMENT.referenceBranch!,
          name: "",
        },
        treatmentBranches: [
          {
            name: "",
            slug: "",
            description: "",
            ratio: 0,
            featureValue: null,
            featureEnabled: false,
          },
        ],
      }}
    />
  ))
  .add("disabled branch", () => (
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        referenceBranch: {
          ...MOCK_EXPERIMENT.referenceBranch!,
          featureEnabled: false,
        },
      }}
    />
  ))
  .add("feature without schema", () => (
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        featureConfig: {
          ...MOCK_EXPERIMENT.featureConfig!,
          schema: null,
        },
      }}
    />
  ))
  .add("missing fields", () => (
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        featureConfig: {
          ...MOCK_EXPERIMENT.featureConfig!,
          schema: "{}",
        },
        referenceBranch: {
          name: "control",
          slug: "control",
          description: "",
          ratio: 0,
          featureValue: null,
          featureEnabled: true,
        },
        treatmentBranches: [],
      }}
    />
  ));
