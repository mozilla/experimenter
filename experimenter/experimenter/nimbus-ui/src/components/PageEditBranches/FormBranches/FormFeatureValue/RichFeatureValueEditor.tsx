/* istanbul ignore file */

import { autocompletion } from "@codemirror/autocomplete";
import { json } from "@codemirror/lang-json";
import { linter } from "@codemirror/lint";
import { EditorState } from "@codemirror/state";
import { EditorView, ViewUpdate } from "@codemirror/view";
import ReactCodeMirror, { ReactCodeMirrorRef } from "@uiw/react-codemirror";
import classNames from "classnames";
import React, { useCallback, useMemo, useRef } from "react";
import { useController, useFormContext } from "react-hook-form";
import { FeatureValueEditorProps } from "src/components/PageEditBranches/FormBranches/FormFeatureValue/props";
import {
  fmlLinter,
  schemaAutocomplete,
  schemaLinter,
} from "src/components/PageEditBranches/FormBranches/FormFeatureValue/validators";

const allowFmlLinting = false;

export default function RichFeatureValueEditor({
  featureConfig,
  defaultValues,
  fieldNamePrefix,
  setSubmitErrors,
  submitErrors,
  errors,
  touched,
  reviewErrors,
  reviewWarnings,
}: FeatureValueEditorProps) {
  const { control } = useFormContext();
  const defaultValue = defaultValues?.value ?? "";
  const { field } = useController({
    control,
    name: `${fieldNamePrefix}.value`,
    defaultValue,
  });

  const hideSubmitErrors = useCallback(() => {
    setSubmitErrors((prevSubmitErrors) => {
      let newSubmitErrors = prevSubmitErrors;
      if (prevSubmitErrors && prevSubmitErrors.value) {
        newSubmitErrors = { ...prevSubmitErrors };
        delete newSubmitErrors.value;
      }
      return newSubmitErrors;
    });
  }, [setSubmitErrors]);

  const editor = useRef<ReactCodeMirrorRef>(null);

  const schema = useMemo<Record<string, unknown> | null>(() => {
    if (!featureConfig.schema) {
      return null;
    }

    try {
      return JSON.parse(featureConfig.schema);
    } catch (e) {
      return null;
    }
  }, [featureConfig.schema]);

  const extensions = useMemo(() => {
    const extensions = [
      json(),
      EditorView.focusChangeEffect.of(
        (state: EditorState, focusing: boolean) => {
          if (!focusing) {
            field.onBlur();
          }

          return null;
        },
      ),
      EditorView.updateListener.of((v: ViewUpdate) => {
        if (v.docChanged) {
          const value = v.state.doc.toString();
          field.onChange(value);
          hideSubmitErrors();
        }
      }),
    ];

    if (schema) {
      if (allowFmlLinting) {
        extensions.push(linter(fmlLinter()));
      } else {
        extensions.push(linter(schemaLinter(schema)));
      }
      const completionSource = schemaAutocomplete(schema);
      if (completionSource) {
        extensions.push(
          autocompletion({
            override: [completionSource],
          }),
        );
      }
    }

    return extensions;
  }, [field, hideSubmitErrors, schema]);

  // We can't use formControlAttrs() because this isn't actually a form component
  // -- it is actually a bunch of divs, so there is no <input> to pass the return
  // value of register() to.
  //
  // Instead we have to build up the class names ourself based on the logic in
  // formControlAttrs.

  return (
    <ReactCodeMirror
      value={defaultValue}
      ref={editor}
      extensions={extensions}
      className={classNames("feature-value-editor", {
        "is-valid":
          !submitErrors?.value?.length && touched.value && !errors?.value,
        "is-invalid":
          submitErrors?.value?.length ||
          ((touched.value ?? false) && (errors.value ?? false)),
        "is-warning":
          reviewWarnings.value?.length || reviewErrors.value?.length,
      })}
    />
  );
}
