/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Button from "react-bootstrap/Button";
import Badge from "react-bootstrap/Badge";
import { ReactComponent as DeleteIcon } from "../../images/x.svg";

import {
  getExperiment_experimentBySlug,
  getExperiment_experimentBySlug_treatmentBranches,
} from "../../types/getExperiment";
import { getConfig_nimbusConfig } from "../../types/getConfig";

/* TODO: EXP-505 for managing branch editing interactions & state */

const FormBranches = ({
  experiment,
  equalRatio,
  featureConfig,
}: {
  experiment: getExperiment_experimentBySlug;
  equalRatio?: boolean;
  featureConfig: getConfig_nimbusConfig["featureConfig"];
}) => {
  const {
    referenceBranch,
    treatmentBranches,
    featureConfig: experimentFeatureConfig,
  } = experiment!;
  return (
    <section data-testid="FormBranches" className="border-top my-3">
      <Form className="p-2">
        <Form.Row className="my-3">
          <Form.Group controlId="evenRatio">
            <Form.Check
              type="checkbox"
              label="Users should be split evenly between all branches"
            />
          </Form.Group>
          <Form.Group as={Col} className="align-top text-right">
            <Button variant="outline-primary" size="sm">
              + Add branch
            </Button>
          </Form.Group>
        </Form.Row>
      </Form>
      <section>
        {referenceBranch && (
          <FormBranch
            {...{
              branch: referenceBranch,
              equalRatio,
              featureConfig,
              experimentFeatureConfig,
              isReference: true,
            }}
          />
        )}
        {treatmentBranches &&
          treatmentBranches.map(
            (branch, idx) =>
              branch && (
                <FormBranch
                  {...{
                    key: `branch-${idx}`,
                    branch,
                    equalRatio,
                    featureConfig,
                    experimentFeatureConfig,
                  }}
                />
              ),
          )}
      </section>

      <div className="d-flex flex-row-reverse bd-highlight">
        <div className="p-2">
          <button className="btn btn-secondary">Next</button>
        </div>
        <div className="p-2">
          <button
            data-testid="submit-button"
            type="submit"
            className="btn btn-primary"
            data-sb-kind="pages/EditBranches"
          >
            <span>Save</span>
          </button>
        </div>
      </div>
    </section>
  );
};

/* TODO: EXP-505 for managing branch editing interactions & state */

export const FormBranch = ({
  branch,
  equalRatio,
  isReference,
  experimentFeatureConfig,
  featureConfig,
}: {
  branch: getExperiment_experimentBySlug_treatmentBranches;
  equalRatio?: boolean;
  isReference?: boolean;
  experimentFeatureConfig: getExperiment_experimentBySlug["featureConfig"];
  featureConfig: getConfig_nimbusConfig["featureConfig"];
}) => {
  const { name, description, ratio, featureValue, featureEnabled } = branch;
  return (
    <Form
      className="mb-3 border border-secondary rounded"
      data-testid="FormBranch"
    >
      <Form.Group className="p-1 mx-3 mt-2 mb-0">
        <Form.Row>
          <Form.Group as={Col} controlId="branch" sm={4} md={3}>
            <Form.Label>
              Branch{" "}
              {isReference && (
                <Badge pill variant="primary" data-testid="control-pill">
                  control
                </Badge>
              )}
            </Form.Label>
            <Form.Control type="text" defaultValue={name} />
          </Form.Group>
          <Form.Group as={Col} controlId="description">
            <Form.Label>Description</Form.Label>
            <Form.Control type="text" defaultValue={description} />
          </Form.Group>
          <Form.Group as={Col} controlId="ratio" sm={2} md={2}>
            <Form.Label>Ratio</Form.Label>
            {equalRatio ? (
              <p data-testid="equal-ratio" className="p-0 m-0">
                Equal
              </p>
            ) : (
              <Form.Control type="text" defaultValue={ratio} />
            )}
          </Form.Group>
          <Form.Group as={Col} sm={1} className="align-top text-right">
            {!isReference && (
              <Button
                variant="light"
                className="bg-transparent border-0 p-0 m-0"
              >
                <DeleteIcon width="18" height="18" />
              </Button>
            )}
          </Form.Group>
        </Form.Row>
      </Form.Group>

      {featureValue === null || !experimentFeatureConfig ? (
        <Form.Group className="px-2 mx-3">
          <Form.Row>
            <Button
              variant="outline-primary"
              size="sm"
              data-testid="feature-config-add"
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
          <p>Feature configuration</p>
          <Form.Row className="align-middle">
            <Form.Group as={Col} controlId="feature">
              <Form.Control
                as="select"
                defaultValue={experimentFeatureConfig.slug}
              >
                <option value="">Select...</option>
                {featureConfig &&
                  featureConfig.map(
                    (feature, idx) =>
                      feature && (
                        <option
                          key={`feature-${feature.slug}-${idx}`}
                          value={feature.slug}
                        >
                          {feature!.name}
                        </option>
                      ),
                  )}
              </Form.Control>
            </Form.Group>
            <Col sm={1} md={1} className="px-2 text-center">
              is
            </Col>
            <Form.Group as={Col} controlId="featureEnabled">
              <Form.Check
                type="switch"
                label={featureEnabled ? "On" : "Off"}
                defaultChecked={featureEnabled}
              />
            </Form.Group>
          </Form.Row>
          {!!experimentFeatureConfig.schema && featureEnabled && (
            <Form.Row data-testid="feature-value-edit">
              <Form.Group as={Col} controlId="featureValue">
                <Form.Label>Value</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={4}
                  defaultValue={featureValue}
                />
              </Form.Group>
            </Form.Row>
          )}
        </Form.Group>
      )}
    </Form>
  );
};

export default FormBranches;
