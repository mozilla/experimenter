/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import FormOverview from ".";
import { MockedCache } from "../../lib/mocks";

export const Subject = ({
  isLoading = false,
  isServerValid = true,
  isMissingField = () => false,
  submitErrors = {},
  onSubmit = () => {},
  onCancel,
  onNext,
  experiment,
}: Partial<React.ComponentProps<typeof FormOverview>>) => {
  const [submitErrorsDefault, setSubmitErrors] = useState<Record<string, any>>(
    submitErrors,
  );
  return (
    <MockedCache>
      <FormOverview
        submitErrors={submitErrorsDefault}
        {...{
          isLoading,
          isServerValid,
          isMissingField,
          setSubmitErrors,
          onSubmit,
          onCancel,
          onNext,
          experiment,
        }}
      />
    </MockedCache>
  );
};
