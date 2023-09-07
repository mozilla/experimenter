/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
import React from "react";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import Row from "react-bootstrap/Row";
import FeatureValueEditor from "src/components/PageEditBranches/FormBranches/FormFeatureValue/FeatureValueEditor";
import { FormFeatureValueProps } from "src/components/PageEditBranches/FormBranches/FormFeatureValue/props";
import { useCommonNestedForm, useConfig } from "src/hooks";

export type { FormFeatureValueProps };

export const featureValueFieldNames = ["featureConfig", "value"] as const;

type FeatureValueFieldName = typeof featureValueFieldNames[number];

export const FormFeatureValue = ({
  featureId,
  ...commonProps
}: FormFeatureValueProps) => {
  const {
    defaultValues,
    errors,
    fieldNamePrefix,
    reviewErrors,
    reviewWarnings,
    setSubmitErrors,
    submitErrors,
    touched,
  } = commonProps;

  const { allFeatureConfigs } = useConfig();
  const { FormErrors, formControlAttrs } =
    useCommonNestedForm<FeatureValueFieldName>(
      defaultValues,
      setSubmitErrors,
      fieldNamePrefix,
      submitErrors,
      errors,
      touched,
      reviewErrors,
      reviewWarnings,
    );

  const featureConfig = allFeatureConfigs?.find(
    (feature) => feature?.id === featureId,
  );
  const fieldName = `${fieldNamePrefix}.value`;
  return (
    <Form.Group data-testid="FormFeatureValue">
      <Form.Control {...formControlAttrs("featureConfig")} hidden />

      <Form.Group id={fieldName} controlId={fieldName}>
        <Form.Label className="w-100">
          <Row className="w-100">
            <Col>
              <span className="text-monospace">{featureConfig?.slug}</span>
            </Col>
          </Row>
        </Form.Label>
        <FeatureValueEditor featureConfig={featureConfig!} {...commonProps} />
        <FormErrors name="value" />
      </Form.Group>
    </Form.Group>
  );
};

export default FormFeatureValue;
