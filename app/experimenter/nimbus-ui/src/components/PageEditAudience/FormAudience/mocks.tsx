/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import { FormAudience } from ".";
import {
  MockedCache,
  MockExperimentContextProvider,
  mockExperimentQuery,
  MOCK_CONFIG,
} from "../../../lib/mocks";
import { getConfig_nimbusConfig } from "../../../types/getConfig";

export const Subject = ({
  config = MOCK_CONFIG,
  submitErrors = {},
  isLoading = false,
  isServerValid = true,
  onSubmit = () => {},
  onNext = () => {},
}: {
  config?: getConfig_nimbusConfig;
} & Partial<React.ComponentProps<typeof FormAudience>>) => {
  const [submitErrorsDefault, setSubmitErrors] = useState<Record<string, any>>(
    submitErrors,
  );
  return (
    <div className="p-5">
      <MockedCache {...{ config }}>
        <MockExperimentContextProvider>
          <FormAudience
            submitErrors={submitErrorsDefault}
            {...{
              setSubmitErrors,
              isLoading,
              isServerValid,
              onSubmit,
              onNext,
            }}
          />
        </MockExperimentContextProvider>
      </MockedCache>
    </div>
  );
};

export const MOCK_EXPERIMENT = mockExperimentQuery("demo-slug").experiment;
