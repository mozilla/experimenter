/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { FormProvider } from "react-hook-form";
import FormScreenshot from ".";
import { useForm } from "../../../../hooks";
import { BranchScreenshotType } from "../../../../types/globalTypes";

export const MOCK_SCREENSHOT: BranchScreenshotType = {
  id: 123,
  description: "This is a screenshot",
  image: "/image/that/was/uploaded",
};

export const Subject = ({
  watcher = () => {},
  defaultValues = MOCK_SCREENSHOT,
  fieldNamePrefix = "treatmentBranches[0].screenshots[0]",
  onRemove = () => {},
  reviewErrors = {},
  reviewWarnings = {},
  setSubmitErrors = () => {},
  submitErrors = {},
}: Partial<React.ComponentProps<typeof FormScreenshot>> & {
  watcher?: (fields: { [x: string]: any }) => void;
}) => {
  const formMethods = useForm(defaultValues);

  const {
    watch,
    formState: { errors, touched },
  } = formMethods;

  watcher(watch());

  return (
    <FormProvider {...formMethods}>
      <div className="p-3">
        <FormScreenshot
          {...{
            defaultValues,
            errors,
            fieldNamePrefix,
            onRemove,
            reviewErrors,
            reviewWarnings,
            setSubmitErrors,
            submitErrors,
            touched,
          }}
        />
      </div>
    </FormProvider>
  );
};
