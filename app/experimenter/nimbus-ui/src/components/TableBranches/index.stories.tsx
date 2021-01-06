/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { Subject, MOCK_EXPERIMENT } from "./mocks";

storiesOf("components/TableBranches", module)
  .add("full branches", () => <Subject />)
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
        treatmentBranches: [
          {
            __typename: "NimbusBranchType",
            name: "",
            slug: "",
            description: "",
            ratio: 0,
            featureValue: null,
            featureEnabled: false,
          },
          ...MOCK_EXPERIMENT.treatmentBranches!,
        ],
      }}
    />
  ));
