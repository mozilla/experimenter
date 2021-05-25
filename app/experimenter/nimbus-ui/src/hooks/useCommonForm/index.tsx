/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { IsDirtyUnsaved, useCommonFormMethods } from "./useCommonFormMethods";
import { useForm } from "./useForm";

export function useCommonForm<FieldNames extends string>(
  defaultValues: Record<string, any>,
  isServerValid: boolean,
  submitErrors: SerializerMessages,
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>,
  reviewMessages?: SerializerMessages,
) {
  const formMethods = useForm(defaultValues);
  const {
    handleSubmit,
    register,
    reset,
    getValues,
    setValue,
    errors,
    control,
    formState: { isSubmitted, isDirty, touched, isValid: isClientValid },
  } = formMethods;

  const isDirtyUnsaved = IsDirtyUnsaved(isDirty, isClientValid, isSubmitted);
  const isValid = isServerValid && isClientValid;

  const { FormErrors, formControlAttrs, formSelectAttrs } =
    useCommonFormMethods<FieldNames>(
      defaultValues,
      setSubmitErrors,
      submitErrors,
      register,
      errors,
      touched,
      reviewMessages,
    );

  return {
    FormErrors,
    formControlAttrs,
    formSelectAttrs,
    handleSubmit,
    reset,
    getValues,
    setValue,
    errors,
    touched,
    isValid,
    isDirtyUnsaved,
    isSubmitted,
    formMethods,
    control,
  };
}
