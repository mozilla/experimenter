/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import classNames from "classnames";
import React from "react";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import { FieldError } from "react-hook-form";
import { useCommonNestedForm } from "../../../hooks";
import { ReactComponent as DeleteIcon } from "../../../images/x.svg";
import { NUMBER_FIELD, REQUIRED_FIELD } from "../../../lib/constants";
import {
  getConfig_nimbusConfig,
  getConfig_nimbusConfig_featureConfig,
} from "../../../types/getConfig";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import { AnnotatedBranch } from "./reducer";

export const branchFieldNames = [
  "name",
  "description",
  "ratio",
  "featureValue",
  "featureEnabled",
  "featureConfig",
] as const;

type BranchFieldName = typeof branchFieldNames[number];

export const FormBranch = ({
  fieldNamePrefix,
  touched,
  errors,
  reviewErrors,
  branch,
  equalRatio,
  isReference,
  experimentFeatureConfig,
  featureConfig,
  onRemove,
  onFeatureConfigChange,
  defaultValues,
  setSubmitErrors,
}: {
  fieldNamePrefix: string;
  touched: Record<string, boolean>;
  errors: Record<string, FieldError>;
  reviewErrors: SerializerSet;
  branch: AnnotatedBranch;
  equalRatio?: boolean;
  isReference?: boolean;
  experimentFeatureConfig: getExperiment_experimentBySlug["featureConfig"];
  featureConfig: getConfig_nimbusConfig["featureConfig"];
  onRemove?: () => void;
  onFeatureConfigChange: (
    featureConfig: getConfig_nimbusConfig_featureConfig | null,
  ) => void;
  defaultValues: Record<string, any>;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
}) => {
  const id = fieldNamePrefix;
  const submitErrors = { ...branch.errors };

  const { FormErrors, formControlAttrs, watch } =
    useCommonNestedForm<BranchFieldName>(
      defaultValues,
      setSubmitErrors,
      fieldNamePrefix,
      submitErrors,
      errors,
      touched,
      reviewErrors,
    );

  const featureEnabled = watch(`${fieldNamePrefix}.featureEnabled`);

  const handleFeatureConfigChange = (
    ev: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const selectedIdx = parseInt(ev.target.value, 10);
    if (isNaN(selectedIdx)) {
      return onFeatureConfigChange(null);
    }
    // featureConfig shouldn't ever be null in practice
    const feature = featureConfig![selectedIdx];
    return onFeatureConfigChange(feature);
  };

  const handleRemoveClick = () => onRemove && onRemove();

  return (
    <div
      className="mb-3 border border-secondary rounded"
      data-testid="FormBranch"
    >
      <Form.Group className="p-1 mx-3 mt-2 mb-0">
        <Form.Row>
          <Form.Group as={Col} controlId={`${id}-name`} sm={4} md={3}>
            <Form.Label>
              Branch{" "}
              {isReference && (
                <Badge pill variant="primary" data-testid="control-pill">
                  control
                </Badge>
              )}
            </Form.Label>
            <Form.Control
              {...formControlAttrs("name", REQUIRED_FIELD)}
              type="text"
            />
            <FormErrors name="name" />
          </Form.Group>
          <Form.Group as={Col} controlId={`${id}-description`}>
            <Form.Label>Description</Form.Label>
            <Form.Control {...formControlAttrs("description")} type="text" />
            <FormErrors name="description" />
          </Form.Group>
          <Form.Group as={Col} controlId={`${id}-ratio`} sm={2} md={2}>
            <Form.Label>Ratio</Form.Label>
            {equalRatio ? (
              <p data-testid="equal-ratio" className="p-0 m-0">
                Equal
                <Form.Control
                  {...formControlAttrs(
                    "ratio",
                    {
                      valueAsNumber: true,
                    },
                    false,
                  )}
                  type="hidden"
                  value="1"
                />
              </p>
            ) : (
              <>
                <Form.Control
                  {...formControlAttrs("ratio", {
                    valueAsNumber: true,
                    ...NUMBER_FIELD,
                  })}
                  type="number"
                  min="1"
                />
                <FormErrors name="ratio" />
              </>
            )}
          </Form.Group>
          <Form.Group as={Col} sm={1} className="align-top text-right">
            {!isReference && onRemove && (
              <Button
                data-testid="remove-branch"
                variant="light"
                className="bg-transparent border-0 p-0 m-0"
                title="Remove branch"
                onClick={handleRemoveClick}
              >
                <DeleteIcon width="18" height="18" />
              </Button>
            )}
          </Form.Group>
        </Form.Row>
      </Form.Group>

      <Form.Group
        className="px-3 pt-2 border-top"
        data-testid="feature-config-edit"
      >
        <Form.Row>
          <Col>
            <Form.Label htmlFor={`${id}-featureConfig`}>
              Feature configuration
            </Form.Label>
          </Col>
        </Form.Row>
        <Form.Row className="align-middle">
          <Form.Group as={Col} controlId={`${id}-featureConfig`}>
            <Form.Control
              as="select"
              data-testid="feature-config-select"
              // Displaying the review-readiness error is handled here instead of `formControlAttrs`
              // due to a state conflict between `react-hook-form` and our internal branch state mangement
              className={classNames(
                reviewErrors.featureConfig?.length > 0 && "is-warning",
              )}
              onChange={handleFeatureConfigChange}
              value={featureConfig!.findIndex(
                (feature) => feature?.slug === experimentFeatureConfig?.slug,
              )}
            >
              <option value="">Select...</option>
              {featureConfig?.map(
                (feature, idx) =>
                  feature && (
                    <option key={`feature-${feature.slug}-${idx}`} value={idx}>
                      {feature.name}
                    </option>
                  ),
              )}
            </Form.Control>
            <FormErrors name="featureConfig" />
          </Form.Group>
          <Col sm={1} md={1} className="px-2 text-center">
            is
          </Col>
          <Form.Group as={Col} controlId={`${id}.featureEnabled`}>
            <Form.Check
              {...formControlAttrs("featureEnabled", {}, false)}
              type="switch"
              label={featureEnabled ? "On" : "Off"}
            />
          </Form.Group>
        </Form.Row>
        {experimentFeatureConfig !== null && featureEnabled ? (
          <Form.Row data-testid="feature-value-edit">
            <Form.Group as={Col} controlId={`${id}-featureValue`}>
              <Form.Label>Value</Form.Label>
              {/* TODO: EXP-732 Maybe do some JSON schema validation here client-side? */}
              <Form.Control
                {...formControlAttrs("featureValue")}
                as="textarea"
                rows={4}
              />
              <FormErrors name="featureValue" />
            </Form.Group>
          </Form.Row>
        ) : (
          <Form.Control
            {...formControlAttrs("featureValue", {}, false)}
            type="hidden"
            value=""
          />
        )}
      </Form.Group>
    </div>
  );
};

export default FormBranch;
