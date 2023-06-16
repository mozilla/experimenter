/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import Row from "react-bootstrap/Row";
import { FieldError } from "react-hook-form";
import { useCommonNestedForm } from "src/hooks";

export const featureValueFieldNames = ["featureConfig", "value"] as const;

type FeatureValueFieldName = typeof featureValueFieldNames[number];

export type FormFeatureValueProps = {
  defaultValues: Record<string, any>;
  errors: Record<string, FieldError>;
  fieldNamePrefix: string;
  reviewErrors: SerializerSet;
  reviewWarnings: SerializerSet;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  submitErrors: { [x: string]: SerializerMessage };
  touched: Record<string, boolean>;
};

export const FormFeatureValue = ({
  defaultValues,
  errors,
  fieldNamePrefix,
  reviewErrors,
  reviewWarnings,
  setSubmitErrors,
  submitErrors,
  touched,
}: FormFeatureValueProps) => {
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

  return (
    <Form.Group data-testid="FormFeatureValue">
      <Form.Control {...formControlAttrs("featureConfig")} hidden />

      <Form.Group controlId={`${fieldNamePrefix}-value`}>
        <Form.Label className="w-100">
          <Row className="w-100">
            <Col>Value</Col>
          </Row>
        </Form.Label>
        <Form.Control {...formControlAttrs("value")} as="textarea" rows={4} />
        <FormErrors name="value" />
      </Form.Group>
    </Form.Group>
  );
};

export default FormFeatureValue;
