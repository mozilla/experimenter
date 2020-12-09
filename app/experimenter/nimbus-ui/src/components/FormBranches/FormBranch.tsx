/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect } from "react";
import { useForm, ValidationRules } from "react-hook-form";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Button from "react-bootstrap/Button";
import Badge from "react-bootstrap/Badge";
import { ReactComponent as DeleteIcon } from "../../images/x.svg";

import { getExperiment_experimentBySlug } from "../../types/getExperiment";

import { getConfig_nimbusConfig } from "../../types/getConfig";

import { AnnotatedBranch } from "./reducer";
import InlineErrorIcon from "../InlineErrorIcon";

type DefaultValues = {
  name: string;
  description: string;
  ratio: string | number;
  featureValue: string | null;
  featureEnabled: boolean;
};

export const FormBranch = ({
  id,
  branch,
  equalRatio,
  isReference,
  experimentFeatureConfig,
  featureConfig,
  lastSubmitTime,
  onRemove,
  onChange,
  onAddFeatureConfig,
  onRemoveFeatureConfig,
  onFeatureConfigChange,
  showMissingIcon,
}: {
  id: string;
  branch: AnnotatedBranch;
  equalRatio?: boolean;
  isReference?: boolean;
  experimentFeatureConfig: getExperiment_experimentBySlug["featureConfig"];
  featureConfig: getConfig_nimbusConfig["featureConfig"];
  lastSubmitTime: number;
  onRemove?: () => void;
  onChange: () => void;
  onAddFeatureConfig: () => void;
  onRemoveFeatureConfig: () => void;
  onFeatureConfigChange: () => void;
  showMissingIcon?: boolean;
}) => {
  const {
    register,
    errors,
    reset,
    trigger,
    formState: { touched },
  } = useForm({
    // Validation will occur automatically onBlur, but we have our own
    // onChange method below which triggers validation on every change.
    mode: "onBlur",
  });

  const { errors: submitErrors, featureEnabled } = branch;

  // Reset the form to branch values whenever the lastSubmitTime changes,
  // clears touched flags and allows new server-side errors to appear
  useEffect(() => {
    const defaultValues: DefaultValues = {
      name: branch.name,
      description: branch.description,
      ratio: branch.ratio,
      featureValue: branch.featureValue,
      featureEnabled: branch.featureEnabled,
    };
    reset(defaultValues);
  }, [branch, reset, lastSubmitTime]);

  // Child form submit is ignored - parent component handles everything.
  const handleSubmit = (ev: React.FormEvent<HTMLElement>) =>
    ev.preventDefault();

  // Validating and reporting branch updates to parent on every field change,
  // because this child form never actually gets submitted
  const handleChange = (
    propertyName: keyof DefaultValues,
    targetAttr: keyof React.ChangeEvent<HTMLInputElement>["target"] = "value",
  ) => async (ev: React.ChangeEvent<HTMLInputElement>) => {
    const value = ev.target[targetAttr];
    const isValid = await trigger();
    onChange({ ...branch, isValid, isDirty: true, [propertyName]: value });
  };

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

  const nameValidated = (
    name: keyof DefaultValues,
    validateRules: ValidationRules = {
      required: "This field may not be blank.",
    },
  ) => ({
    name,
    ref: register(validateRules),
    isInvalid:
      // Server-side errors signal invalid when field is freshly reset
      (!touched[name] && !!submitErrors[name]) ||
      // Client-side errors signal invalid after a field has been touched
      (touched[name] && !!errors[name]),
    isValid:
      // Valid after touched and no client-side errors
      touched[name] && !errors[name],
  });

  const FormErrors = ({ name }: { name: keyof DefaultValues }) => (
    <>
      {errors[name] && (
        <Form.Control.Feedback type="invalid" data-for={`${id}-name`}>
          {errors[name]!.message}
        </Form.Control.Feedback>
      )}
      {!touched[name] && submitErrors[name] && (
        <Form.Control.Feedback type="invalid" data-for={`${id}-name`}>
          {submitErrors[name]}
        </Form.Control.Feedback>
      )}
    </>
  );

  return (
    <Form
      className="mb-3 border border-secondary rounded"
      data-testid="FormBranch"
      onSubmit={handleSubmit}
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
              {...nameValidated("name")}
              type="text"
              onChange={handleChange("name")}
            />
            <FormErrors name="name" />
          </Form.Group>
          <Form.Group as={Col} controlId={`${id}-description`}>
            <Form.Label>Description</Form.Label>
            <Form.Control
              {...nameValidated("description")}
              type="text"
              onChange={handleChange("description")}
            />
            <FormErrors name="description" />
          </Form.Group>
          <Form.Group as={Col} controlId={`${id}-ratio`} sm={2} md={2}>
            <Form.Label>Ratio</Form.Label>
            {equalRatio ? (
              <p data-testid="equal-ratio" className="p-0 m-0">
                Equal
              </p>
            ) : (
              <>
                <Form.Control
                  {...nameValidated("ratio", {
                    required: "Ratio may not be blank.",
                    pattern: {
                      value: /^\d+$/,
                      message: "Ratio must be a number",
                    },
                  })}
                  type="number"
                  min="1"
                  onChange={handleChange("ratio")}
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

            {showMissingIcon && (
              <InlineErrorIcon
                name="control"
                message="A control branch is required"
              />
            )}
          </Form.Group>
        </Form.Row>
      </Form.Group>

      {experimentFeatureConfig === null ? (
        <Form.Group className="px-2 mx-3">
          <Form.Row>
            <Button
              variant="outline-primary"
              size="sm"
              data-testid="feature-config-add"
              onClick={onAddFeatureConfig}
            >
              + Feature configuration
            </Button>
          </Form.Row>
        </Form.Group>
      ) : (
        <Form.Group
          className="px-3 py-2 border-top"
          data-testid="feature-config-edit"
        >
          <Form.Row>
            <Col className="px-2">Feature configuration</Col>
            <Form.Group as={Col} sm={1} className="align-top text-right">
              <Button
                variant="light"
                className="bg-transparent border-0 p-0 m-0"
                data-testid="feature-config-remove"
                title="Remove feature configuration"
                onClick={onRemoveFeatureConfig}
              >
                <DeleteIcon width="18" height="18" />
              </Button>
            </Form.Group>
          </Form.Row>
          <Form.Row className="align-middle">
            <Form.Group as={Col} controlId={`${id}-feature`}>
              <Form.Control
                as="select"
                data-testid="feature-config-select"
                onChange={handleFeatureConfigChange}
                value={featureConfig!.findIndex(
                  (feature) => feature?.slug === experimentFeatureConfig?.slug,
                )}
              >
                <option value="">Select...</option>
                {featureConfig?.map(
                  (feature, idx) =>
                    feature && (
                      <option
                        key={`feature-${feature.slug}-${idx}`}
                        value={idx}
                      >
                        {feature.name}
                      </option>
                    ),
                )}
              </Form.Control>
            </Form.Group>
            <Col sm={1} md={1} className="px-2 text-center">
              is
            </Col>
            <Form.Group as={Col} controlId={`${id}-featureEnabled`}>
              <Form.Check
                type="switch"
                label={featureEnabled ? "On" : "Off"}
                defaultChecked={featureEnabled}
                onChange={handleChange("featureEnabled", "checked")}
              />
            </Form.Group>
          </Form.Row>
          {experimentFeatureConfig !== null &&
            !!experimentFeatureConfig.schema &&
            featureEnabled && (
              <Form.Row data-testid="feature-value-edit">
                <Form.Group as={Col} controlId={`${id}-featureValue`}>
                  <Form.Label>Value</Form.Label>
                  {/* TODO: Maybe do some JSON schema validation here client-side? */}
                  <Form.Control
                    {...nameValidated("featureValue")}
                    as="textarea"
                    rows={4}
                    onChange={handleChange("featureValue")}
                  />
                  <FormErrors name="featureValue" />
                </Form.Group>
              </Form.Row>
            )}
        </Form.Group>
      )}
    </Form>
  );
};

export default FormBranch;
