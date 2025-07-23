import React from "react";
import Form from "react-bootstrap/Form";
import { FeatureValueEditorProps } from "src/components/PageEditBranches/FormBranches/FormFeatureValue/props";
import RichFeatureValueEditor from "src/components/PageEditBranches/FormBranches/FormFeatureValue/RichFeatureValueEditor";
import { useCommonNestedForm } from "src/hooks";

let FeatureValueEditor: (props: FeatureValueEditorProps) => JSX.Element;

if (process.env.JEST_WORKER_ID !== undefined) {
  // In testing environments, just provide a plain textarea because our rich text
  // control cannot be tested inside an artificial DOM environment.
  FeatureValueEditor = function FeatureValueEditor({
    defaultValues,
    setSubmitErrors,
    fieldNamePrefix,
    submitErrors,
    errors,
    touched,
    reviewErrors,
    reviewWarnings,
  }: FeatureValueEditorProps) {
    const { formControlAttrs } = useCommonNestedForm<"value">(
      defaultValues,
      setSubmitErrors,
      fieldNamePrefix,
      submitErrors,
      errors,
      touched,
      reviewErrors,
      reviewWarnings,
    );
    return (
      <Form.Control as="textarea" rows={4} {...formControlAttrs("value")} />
    );
  };
} else {
  /* istanbul ignore next */
  FeatureValueEditor = RichFeatureValueEditor;
}

export default FeatureValueEditor;
