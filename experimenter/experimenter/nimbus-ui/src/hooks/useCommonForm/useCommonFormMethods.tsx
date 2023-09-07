/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React from "react";
import Form from "react-bootstrap/Form";
import { FieldError, RegisterOptions, UseFormMethods } from "react-hook-form";
import { camelToSnakeCase } from "src/lib/caseConversions";

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
  submitErrors: SerializerMessages,
  register: UseFormMethods["register"],
  errors: UseFormMethods["errors"],
  touched: UseFormMethods["formState"]["touched"],
  reviewMessages: SerializerMessages = {},
  reviewWarnings: SerializerMessages = {},
) {
  const hideSubmitError = <K extends FieldNames>(name: K) => {
    if (submitErrors && submitErrors[camelToSnakeCase(name)]) {
      const modifiedSubmitErrors = { ...submitErrors };
      delete modifiedSubmitErrors[camelToSnakeCase(name)];
      setSubmitErrors(modifiedSubmitErrors);
    }
  };

  // Fields are optional by default. Pass `REQUIRED_FIELD` into `registerOptions`
  // to require a valid field before form submission is allowed.
  const formControlAttrs = <K extends FieldNames>(
    name: K,
    registerOptions: RegisterOptions = {},
    setDefaultValue = true,
    prefix?: string,
  ) => {
    const snakeCaseName = camelToSnakeCase(name);
    const fieldName = prefix ? `${prefix}.${name}` : name;
    const hasReviewMessage = (reviewMessages[snakeCaseName] || []).length > 0;
    const hasReviewWarning = (reviewWarnings[snakeCaseName] || []).length > 0;

    return {
      "data-testid": fieldName,
      name: fieldName,
      ref: register(registerOptions),
      className: classNames({
        "is-warning": hasReviewMessage || hasReviewWarning,
      }),
      // setting `setDefaultValue = false` is handy when an input needs a default
      // value via `value` instead of `defaultValue` or if the value is boolean,
      // usually for hidden form fields or checkbox inputs
      ...(setDefaultValue && {
        defaultValue: defaultValues[name],
        onChange: () => hideSubmitError(name),
        isInvalid: Boolean(
          submitErrors![snakeCaseName] || (touched[name] && errors[name]),
        ),
        isValid: Boolean(
          !submitErrors![snakeCaseName] && touched[name] && !errors[name],
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
    const snakeCaseName = camelToSnakeCase(name);
    const fieldName = prefix ? `${prefix}.${name}` : name;
    const fieldReviewMessages =
      (
        reviewMessages as SerializerMessages<
          SerializerMessage | SerializerSet[]
        >
      )[snakeCaseName] || [];
    const fieldReviewWarnings =
      (
        reviewWarnings as SerializerMessages<
          SerializerMessage | SerializerSet[]
        >
      )[snakeCaseName] || [];
    return (
      <>
        {fieldReviewMessages.length > 0 && (
          // @ts-ignore This component doesn't technically support type="warning", but
          // all it's doing is using the string in a class, so we can safely override.
          <Form.Control.Feedback type="warning" data-for={fieldName}>
            {fieldReviewMessages.join(", ")}
          </Form.Control.Feedback>
        )}
        {fieldReviewWarnings.length > 0 && (
          // @ts-ignore This component doesn't technically support type="warning", but
          // all it's doing is using the string in a class, so we can safely override.
          <Form.Control.Feedback type="warning" data-for={fieldName}>
            {fieldReviewWarnings.join(", ")}
          </Form.Control.Feedback>
        )}
        {errors[name] && (
          <Form.Control.Feedback type="invalid" data-for={fieldName}>
            {(errors[name] as FieldError).message}
          </Form.Control.Feedback>
        )}
        {submitErrors![snakeCaseName] && (
          <Form.Control.Feedback type="invalid" data-for={fieldName}>
            {submitErrors![snakeCaseName]}
          </Form.Control.Feedback>
        )}
        {/* for testing - can't wrap the errors in a container with a test ID
      because of Bootstrap's adjacent class CSS rules, error won't be shown */}
        {!errors[name] && !submitErrors![snakeCaseName] && (
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
    className: classNames(
      (submitErrors![camelToSnakeCase(name)] ||
        (touched[name] && errors[name])) &&
        "is-invalid border border-danger rounded",
      (reviewMessages[camelToSnakeCase(name)] || []).length > 0 &&
        "is-warning border-feedback-warning rounded",
    ),
  });

  return {
    formControlAttrs,
    formSelectAttrs,
    FormErrors,
  };
}
