/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { RegisterOptions, FieldError } from "react-hook-form";
import Form from "react-bootstrap/Form";
import { useForm } from "react-hook-form";

// TODO: 'any' type on `onChange={(selectedOptions) => ...`,
// it wants this, but can't seem to coerce it into SelectOption type
// type SelectedOption = {
//   value: ValueType<any, true>;
//   action: ActionMeta<any>;
// };
export type SelectOption = { label: string; value: string };

export function useCommonForm<FieldNames extends string>(
  defaultValues: Record<string, any>,
  isServerValid: boolean,
  submitErrors: Record<string, string[]>,
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>,
) {
  const {
    handleSubmit,
    register,
    reset,
    errors,
    formState: { isSubmitted, isDirty, touched, isValid: isClientValid },
  } = useForm({
    mode: "onTouched",
    defaultValues,
  });

  const isValid = isServerValid && isClientValid;
  const isDirtyUnsaved = isDirty && !(isValid && isSubmitted);

  const hideSubmitError = <K extends FieldNames>(name: K) => {
    if (submitErrors[name]) {
      const modifiedSubmitErrors = { ...submitErrors };
      delete modifiedSubmitErrors[name];
      setSubmitErrors(modifiedSubmitErrors);
    }
  };

  // Fields are required by default. Pass an empty object `{}` as `registerOptions`
  // to allow form submission without that field being required.
  const formControlAttrs = <K extends FieldNames>(
    name: K,
    registerOptions: RegisterOptions = {
      required: "This field may not be blank.",
    },
  ) => ({
    name,
    "data-testid": name,
    ref: register(registerOptions),
    defaultValue: defaultValues[name],
    onChange: () => hideSubmitError(name),
    isInvalid: Boolean(submitErrors[name] || (touched[name] && errors[name])),
    isValid: Boolean(!submitErrors[name] && touched[name] && !errors[name]),
  });

  const getValuesFromOptions = (selectedOptions: SelectOption[] | null) =>
    selectedOptions?.map((option) => option?.value) || [];

  /* <Select /> handles `register` internally and only renders certain props.
   * Prefer `<Form.Control as="select">` with `formControlAttrs` instead and
   * only use this for multiselects using the `react-select` package.
   */
  const formSelectAttrs = <K extends FieldNames>(
    name: K,
    setValuesFromOptions: React.Dispatch<React.SetStateAction<string[]>>,
  ) => ({
    defaultValue: defaultValues[name],
    onChange: (selectedOptions: any) => {
      setValuesFromOptions(getValuesFromOptions(selectedOptions));
      hideSubmitError(name);
    },
    className: Boolean(submitErrors[name] || (touched[name] && errors[name]))
      ? "is-invalid border border-danger rounded"
      : "",
  });

  const FormErrors = <K extends FieldNames>({ name }: { name: K }) => (
    <>
      {errors[name] && (
        <Form.Control.Feedback type="invalid" data-for={name}>
          {(errors[name] as FieldError).message}
        </Form.Control.Feedback>
      )}
      {submitErrors[name] && (
        <Form.Control.Feedback type="invalid" data-for={name}>
          {submitErrors[name]}
        </Form.Control.Feedback>
      )}
      {/* for testing - can't wrap the errors in a container with a test ID
      because of Bootstrap's adjacent class CSS rules */}
      {!errors[name] && !submitErrors[name] && (
        <span data-testid={`${name}-form-errors`} />
      )}
    </>
  );

  return {
    FormErrors,
    formControlAttrs,
    formSelectAttrs,
    handleSubmit,
    reset,
    isValid,
    isDirtyUnsaved,
    isSubmitted,
  };
}
