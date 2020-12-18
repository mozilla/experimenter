/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import { mockExperimentQuery } from "../../lib/mocks";
import { FormAudience } from ".";
import { MOCK_CONFIG, MockedCache } from "../../lib/mocks";
import { getConfig_nimbusConfig } from "../../types/getConfig";

export const Subject = ({
  config = MOCK_CONFIG,
  experiment = MOCK_EXPERIMENT,
  submitErrors = {},
  isMissingField = () => false,
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
        <FormAudience
          submitErrors={submitErrorsDefault}
          {...{
            experiment,
            setSubmitErrors,
            isMissingField,
            isLoading,
            isServerValid,
            onSubmit,
            onNext,
          }}
        />
      </MockedCache>
    </div>
  );
};

export const MOCK_EXPERIMENT = mockExperimentQuery("demo-slug").experiment;
