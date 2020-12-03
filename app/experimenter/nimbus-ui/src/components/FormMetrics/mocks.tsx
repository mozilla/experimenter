/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import FormMetrics from ".";
import { MockedCache, mockExperimentQuery, MOCK_CONFIG } from "../../lib/mocks";

export const Subject = ({
  isLoading = false,
  isServerValid = true,
  submitErrors = {},
  onSave = () => {},
  onNext = () => {},
  experiment = mockExperimentQuery("boo").data,
  probeSets = MOCK_CONFIG.probeSets,
}: Partial<React.ComponentProps<typeof FormMetrics>>) => (
  <MockedCache>
    <FormMetrics
      {...{
        isLoading,
        isServerValid,
        submitErrors,
        onSave,
        onNext,
        experiment,
        probeSets,
      }}
    />
  </MockedCache>
);
