/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import FormOverview from ".";
import { MockedCache, MOCK_CONFIG } from "../../lib/mocks";
import { getConfig_nimbusConfig } from "../../types/getConfig";

export const Subject = ({
  isLoading = false,
  isServerValid = true,
  submitErrors = {},
  onSubmit = () => {},
  onCancel,
  experiment,
  config = MOCK_CONFIG,
}: {
  config?: getConfig_nimbusConfig;
} & Partial<React.ComponentProps<typeof FormOverview>>) => {
  const [submitErrorsDefault, setSubmitErrors] =
    useState<Record<string, any>>(submitErrors);
  return (
    <MockedCache {...{ config }}>
      <FormOverview
        submitErrors={submitErrorsDefault}
        {...{
          isLoading,
          isServerValid,
          setSubmitErrors,
          onSubmit,
          onCancel,
          experiment,
        }}
      />
    </MockedCache>
  );
};
