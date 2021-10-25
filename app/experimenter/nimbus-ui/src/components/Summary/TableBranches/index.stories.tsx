/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import { MOCK_SCREENSHOTS } from "../mocks";
import { MOCK_EXPERIMENT, Subject } from "./mocks";

storiesOf("components/Summary/TableBranches", module)
  .add("full branches", () => (
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        referenceBranch: {
          ...MOCK_EXPERIMENT.referenceBranch!,
          screenshots: MOCK_SCREENSHOTS,
        },
        treatmentBranches: MOCK_EXPERIMENT.treatmentBranches!.map((branch) => ({
          ...branch!,
          screenshots: MOCK_SCREENSHOTS,
        })),
      }}
    />
  ))
  .add("one branch", () => (
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        treatmentBranches: [
          {
            id: null,
            name: "",
            slug: "",
            description: "",
            ratio: 0,
            featureValue: null,
            featureEnabled: false,
            screenshots: [],
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
          slug: "",
        },
        treatmentBranches: [
          {
            id: null,
            name: "",
            slug: "",
            description: "",
            ratio: 0,
            featureValue: null,
            featureEnabled: false,
            screenshots: [],
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
          ...MOCK_EXPERIMENT.referenceBranch!,
          id: 456,
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
