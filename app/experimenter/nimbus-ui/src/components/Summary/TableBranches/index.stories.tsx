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

            featureValues: [
              {
                featureConfig: MOCK_EXPERIMENT.featureConfigs![0],
                enabled: false,
                value: null,
              },
            ],
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
            featureValues: [
              {
                featureConfig: MOCK_EXPERIMENT.featureConfigs![0],
                enabled: false,
                value: null,
              },
            ],
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
          featureValues: [
            {
              ...MOCK_EXPERIMENT.referenceBranch!.featureValues![0],
              enabled: false,
            },
          ],
        },
      }}
    />
  ))
  .add("missing fields", () => (
    <Subject
      experiment={{
        ...MOCK_EXPERIMENT,
        referenceBranch: {
          ...MOCK_EXPERIMENT.referenceBranch!,
          id: 456,
          name: "control",
          slug: "control",
          description: "",
          ratio: 0,
          featureValues: [
            {
              featureConfig: MOCK_EXPERIMENT.featureConfigs![0],
              enabled: true,
              value: null,
            },
          ],
        },
        treatmentBranches: [],
      }}
    />
  ));
