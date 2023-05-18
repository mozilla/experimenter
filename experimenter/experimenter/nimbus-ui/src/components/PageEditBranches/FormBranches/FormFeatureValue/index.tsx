/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import Row from "react-bootstrap/Row";
import { FieldError } from "react-hook-form";
import { useCommonNestedForm, useConfig } from "src/hooks";

export const featureValueFieldNames = ["featureConfig", "value"] as const;

type FeatureValueFieldName = typeof featureValueFieldNames[number];

export type FormFeatureValueProps = {
  defaultValues: Record<string, any>;
  errors: Record<string, FieldError>;
  featureId: number;
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
  featureId,
  reviewErrors,
  reviewWarnings,
  setSubmitErrors,
  submitErrors,
  touched,
}: FormFeatureValueProps) => {
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

  const featureSlug = allFeatureConfigs?.find(
    (feature) => feature?.id === featureId,
  )?.slug;

  return (
    <Form.Group data-testid="FormFeatureValue">
      <Form.Control {...formControlAttrs("featureConfig")} hidden />

      <Form.Group controlId={`${fieldNamePrefix}-value`}>
        <Form.Label className="w-100">
          <Row className="w-100">
            <Col>
              <span className="text-monospace">{featureSlug}</span>
            </Col>
          </Row>
        </Form.Label>
        <Form.Control {...formControlAttrs("value")} as="textarea" rows={4} />
        <FormErrors name="value" />
      </Form.Group>
    </Form.Group>
  );
};

export default FormFeatureValue;
