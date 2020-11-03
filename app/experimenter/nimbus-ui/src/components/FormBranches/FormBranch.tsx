/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Button from "react-bootstrap/Button";
import Badge from "react-bootstrap/Badge";
import { ReactComponent as DeleteIcon } from "../../images/x.svg";

import { getExperiment_experimentBySlug } from "../../types/getExperiment";

import {
  getConfig_nimbusConfig,
  getConfig_nimbusConfig_featureConfig,
} from "../../types/getConfig";

import { AnnotatedBranch } from "./reducer";

export const FormBranch = ({
  id,
  branch,
  equalRatio,
  isReference,
  experimentFeatureConfig,
  featureConfig,
  onRemove,
  onChange,
  onAddFeatureConfig,
  onRemoveFeatureConfig,
  onFeatureConfigChange,
}: {
  id: string;
  branch: AnnotatedBranch;
  equalRatio?: boolean;
  isReference?: boolean;
  experimentFeatureConfig: getExperiment_experimentBySlug["featureConfig"];
  featureConfig: getConfig_nimbusConfig["featureConfig"];
  onRemove?: () => void;
  onChange: (branch: AnnotatedBranch) => void;
  onAddFeatureConfig: () => void;
  onRemoveFeatureConfig: () => void;
  onFeatureConfigChange: (
    featureConfig: getConfig_nimbusConfig_featureConfig | null,
  ) => void;
}) => {
  const { name, description, ratio, featureValue, featureEnabled } = branch;

  const handleRemoveClick = () => {
    onRemove && onRemove();
  };

  const handleChange = (
    propertyName: string,
    targetAttr: keyof React.ChangeEvent<HTMLInputElement>["target"] = "value",
  ) => (ev: React.ChangeEvent<HTMLInputElement>) => {
    onChange({
      ...branch,
      [propertyName]: ev.target[targetAttr],
    });
  };

  const handleFeatureConfigChange = (
    ev: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const selectedIdx = ev.target.value;
    if (selectedIdx === "") {
      return onFeatureConfigChange(null);
    }
    const feature = featureConfig![parseInt(selectedIdx, 10)];
    return onFeatureConfigChange(feature);
  };

  return (
    <Form
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
              type="text"
              defaultValue={name}
              onChange={handleChange("name")}
            />
          </Form.Group>
          <Form.Group as={Col} controlId={`${id}-description`}>
            <Form.Label>Description</Form.Label>
            <Form.Control
              type="text"
              defaultValue={description}
              onChange={handleChange("description")}
            />
          </Form.Group>
          <Form.Group as={Col} controlId={`${id}-ratio`} sm={2} md={2}>
            <Form.Label>Ratio</Form.Label>
            {equalRatio ? (
              <p data-testid="equal-ratio" className="p-0 m-0">
                Equal
              </p>
            ) : (
              <Form.Control
                type="text"
                defaultValue={ratio}
                onChange={handleChange("ratio")}
              />
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
                  <Form.Control
                    as="textarea"
                    rows={4}
                    defaultValue={"" + featureValue}
                    onChange={handleChange("featureValue")}
                  />
                </Form.Group>
              </Form.Row>
            )}
        </Form.Group>
      )}
    </Form>
  );
};

export default FormBranch;
