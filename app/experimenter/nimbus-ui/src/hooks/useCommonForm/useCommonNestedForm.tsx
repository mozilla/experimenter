/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import {
  RegisterOptions,
  useFormContext,
  UseFormMethods,
} from "react-hook-form";
import { useCommonFormMethods } from "./useCommonFormMethods";

export function useCommonNestedForm<FieldNames extends string>(
  defaultValues: Record<string, any>,
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>,
  prefix: string,
  nestedSubmitErrors: Record<string, string[]>,
  nestedErrors: UseFormMethods["errors"],
  nestedTouched: UseFormMethods["formState"]["touched"],
  nestedReviewMessages: Record<string, string[]> = {},
) {
  const { register, watch } = useFormContext();

  const { FormErrors, formControlAttrs } = useCommonFormMethods<FieldNames>(
    defaultValues,
    setSubmitErrors,
    nestedSubmitErrors,
    register,
    nestedErrors,
    nestedTouched,
    nestedReviewMessages,
  );

  const NestedFormErrors = <K extends FieldNames>({ name }: { name: K }) => (
    <FormErrors {...{ name, prefix }} />
  );

  const nestedFormControlAttrs = <K extends FieldNames>(
    name: K,
    registerOptions?: RegisterOptions,
    setDefaultValue?: boolean,
  ) => formControlAttrs(name, registerOptions, setDefaultValue, prefix);

  return {
    FormErrors: NestedFormErrors,
    formControlAttrs: nestedFormControlAttrs,
    watch,
  };
}
