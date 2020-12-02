/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";
import { FormAudience } from ".";

export const Subject = ({
  experiment = MOCK_EXPERIMENT,
  config = MOCK_CONFIG,
}: Partial<React.ComponentProps<typeof FormAudience>>) => (
  <div className="p-5">
    <FormAudience
      {...{
        experiment,
        config,
      }}
    />
  </div>
);

export const MOCK_EXPERIMENT = mockExperimentQuery("demo-slug")!.data!;
