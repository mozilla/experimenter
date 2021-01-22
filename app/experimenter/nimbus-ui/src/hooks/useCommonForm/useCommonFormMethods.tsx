/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Form from "react-bootstrap/Form";
import { FieldError, RegisterOptions, UseFormMethods } from "react-hook-form";
import { camelToSnakeCase } from "../../lib/caseConversions";

// TODO: 'any' type on `onChange={(selectedOptions) => ...`,
// it wants this, but can't seem to coerce it into SelectOption type
// type SelectedOption = {
//   value: ValueType<any, true>;
//   action: ActionMeta<any>;
// };

export type SelectOption = { label: string; value: string };

export const IsDirtyUnsaved = (
  isDirty: boolean,
  isValid: boolean,
  isSubmitted: boolean,
) => isDirty && !(isValid && isSubmitted);

export function useCommonFormMethods<FieldNames extends string>(
  defaultValues: Record<string, any>,
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>,
  submitErrors: Record<string, string[]>,
  register: UseFormMethods["register"],
  errors: UseFormMethods["errors"],
  touched: UseFormMethods["formState"]["touched"],
) {
  const hideSubmitError = <K extends FieldNames>(name: K) => {
    if (submitErrors && submitErrors[camelToSnakeCase(name)]) {
      const modifiedSubmitErrors = { ...submitErrors };
      delete modifiedSubmitErrors[camelToSnakeCase(name)];
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
    setDefaultValue = true,
    prefix?: string,
  ) => {
    const fieldName = prefix ? `${prefix}.${name}` : name;
    return {
      "data-testid": fieldName,
      name: fieldName,
      ref: register(registerOptions),
      // setting `setDefaultValue = false` is handy when an input needs a default
      // value via `value` instead of `defaultValue` or if the value is boolean,
      // usually for hidden form fields or checkbox inputs
      ...(setDefaultValue && {
        defaultValue: defaultValues[name],
        onChange: () => hideSubmitError(name),
        isInvalid: Boolean(
          submitErrors![camelToSnakeCase(name)] ||
            (touched[name] && errors[name]),
        ),
        isValid: Boolean(
          !submitErrors![camelToSnakeCase(name)] &&
            touched[name] &&
            !errors[name],
        ),
      }),
    };
  };

  const FormErrors = <K extends FieldNames>({
    name,
    prefix,
  }: {
    name: K;
    prefix?: string;
  }) => {
    const fieldName = prefix ? `${prefix}.${name}` : name;
    return (
      <>
        {errors[name] && (
          <Form.Control.Feedback type="invalid" data-for={fieldName}>
            {(errors[name] as FieldError).message}
          </Form.Control.Feedback>
        )}
        {submitErrors![camelToSnakeCase(name)] && (
          <Form.Control.Feedback type="invalid" data-for={fieldName}>
            {submitErrors![camelToSnakeCase(name)]}
          </Form.Control.Feedback>
        )}
        {/* for testing - can't wrap the errors in a container with a test ID
      because of Bootstrap's adjacent class CSS rules, error won't be shown */}
        {!errors[name] && !submitErrors![camelToSnakeCase(name)] && (
          <span data-testid={`${fieldName}-form-errors`} />
        )}
      </>
    );
  };

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
    onChange: (selectedOptions: any /* TODO, see top of file */) => {
      setValuesFromOptions(getValuesFromOptions(selectedOptions));
      hideSubmitError(name);
    },
    className: Boolean(
      submitErrors![camelToSnakeCase(name)] || (touched[name] && errors[name]),
    )
      ? "is-invalid border border-danger rounded"
      : "",
  });

  return {
    formControlAttrs,
    formSelectAttrs,
    FormErrors,
  };
}
