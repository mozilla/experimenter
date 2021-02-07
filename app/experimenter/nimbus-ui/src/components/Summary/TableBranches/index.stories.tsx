/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { storiesOf } from "@storybook/react";
import React from "react";
import { MOCK_EXPERIMENT, Subject } from "./mocks";

storiesOf("components/Summary/TableBranches", module)
  .add("full branches", () => <Subject />)
  .add("disabled branch", () => (
    <Subject
      experiment={{
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
