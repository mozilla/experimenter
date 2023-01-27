/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import FormMetrics from "src/components/PageEditMetrics/FormMetrics";
import { MockedCache, mockExperimentQuery } from "src/lib/mocks";

export const Subject = ({
  isLoading = false,
  isServerValid = true,
  submitErrors = {},
  onSave = () => {},
  experiment = mockExperimentQuery("boo").experiment,
}: Partial<React.ComponentProps<typeof FormMetrics>>) => {
  const [submitErrorsDefault, setSubmitErrors] =
    useState<SerializerMessages>(submitErrors);
  return (
    <MockedCache>
      <FormMetrics
        submitErrors={submitErrorsDefault}
        {...{
          isLoading,
          isServerValid,
          setSubmitErrors,
          onSave,
          experiment,
        }}
      />
    </MockedCache>
  );
};
