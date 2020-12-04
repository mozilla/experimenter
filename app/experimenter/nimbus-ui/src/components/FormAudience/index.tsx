/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Select from "react-select";
import Form from "react-bootstrap/Form";
import InputGroup from "react-bootstrap/InputGroup";
import Col from "react-bootstrap/Col";
import LinkExternal from "../LinkExternal";
import InlineErrorIcon from "../InlineErrorIcon";

import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  getConfig_nimbusConfig,
  getConfig_nimbusConfig_channels,
} from "../../types/getConfig";

// TODO: find this doco URL
const AUDIENCE_DOC_URL =
  "https://mana.mozilla.org/wiki/pages/viewpage.action?spaceKey=FJT&title=Project+Nimbus";

type FormAudienceConfig = Pick<
  getConfig_nimbusConfig,
  "channels" | "firefoxMinVersion" | "targetingConfigSlug"
>;

export const FormAudience = ({
  experiment,
  config,
  isMissingField,
}: {
  experiment: getExperiment_experimentBySlug;
  config: FormAudienceConfig;
  isMissingField: (fieldName: string) => boolean;
}) => {
  const {
    channels,
    firefoxMinVersion,
    targetingConfigSlug,
    populationPercent,
    totalEnrolledClients,
    proposedEnrollment,
    proposedDuration,
  } = experiment;

  const channelsOptions = config.channels?.filter(
    (item): item is getConfig_nimbusConfig_channels => item !== null,
  );
  const channelsDefaultValue = channels?.map((channel) =>
    channelsOptions?.find((option) => option?.value === channel),
  );

  return (
    <Form data-testid="FormAudience">
      <Form.Group>
        <Form.Row>
          <Form.Group as={Col} controlId="channel" md={8} lg={8}>
            <Form.Label className="d-flex align-items-center">
              Channel
              {isMissingField("channels") && (
                <InlineErrorIcon
                  name="channels"
                  message="At least one channel must be selected"
                />
              )}
            </Form.Label>
            <Select
              isMulti
              name="channel"
              data-testid="channel"
              defaultValue={channelsDefaultValue}
              options={channelsOptions}
            />
          </Form.Group>
          <Form.Group as={Col} controlId="minVersion">
            <Form.Label className="d-flex align-items-center">
              Min Version
              {isMissingField("firefox_min_version") && (
                <InlineErrorIcon
                  name="ff-min"
                  message="A minimum Firefox version must be selected"
                />
              )}
            </Form.Label>
            <Form.Control
              as="select"
              data-testid="minVersion"
              defaultValue={firefoxMinVersion || ""}
            >
              <SelectOptions options={config.firefoxMinVersion} />
            </Form.Control>
          </Form.Group>
        </Form.Row>
        <Form.Row>
          <Form.Group as={Col} controlId="targeting">
            <Form.Label className="d-flex align-items-center">
              Advanced Targeting
              {isMissingField("targeting_config_slug") && (
                <InlineErrorIcon
                  name="config"
                  message="A targeting config must be selected"
                />
              )}
            </Form.Label>
            <Form.Control
              as="select"
              data-testid="targeting"
              defaultValue={targetingConfigSlug || ""}
            >
              <SelectOptions options={config.targetingConfigSlug} />
            </Form.Control>
          </Form.Group>
        </Form.Row>
      </Form.Group>

      <Form.Group className="bg-light p-4">
        <p className="text-secondary">
          Please ask a data scientist to help you determine these values.{" "}
          <LinkExternal href={AUDIENCE_DOC_URL}>Learn more</LinkExternal>
        </p>

        <Form.Row>
          <Form.Group as={Col} className="mx-5" controlId="clientsPercent">
            <Form.Label>Percent of clients</Form.Label>
            <InputGroup>
              <Form.Control
                placeholder="0.00"
                aria-describedby="clientsPercent-unit"
                type="text"
                defaultValue={populationPercent || 0}
              />
              <InputGroup.Append>
                <InputGroup.Text id="clientsPercent-unit">%</InputGroup.Text>
              </InputGroup.Append>
            </InputGroup>
          </Form.Group>

          <Form.Group as={Col} className="mx-5" controlId="clientsNumber">
            <Form.Label>Expected number of clients</Form.Label>
            <Form.Control
              name="clientsNumber"
              placeholder="0"
              type="text"
              defaultValue={totalEnrolledClients}
            />
          </Form.Group>
        </Form.Row>

        <Form.Row>
          <Form.Group as={Col} className="mx-5" controlId="enrollmentPeriod">
            <Form.Label className="d-flex align-items-center">
              Enrollment period
              {isMissingField("proposed_enrollment") && (
                <InlineErrorIcon
                  name="enrollment"
                  message="Proposed enrollment cannot be blank"
                />
              )}
            </Form.Label>
            <InputGroup>
              <Form.Control
                placeholder="7"
                aria-describedby="enrollmentPeriod-unit"
                defaultValue={proposedEnrollment || 7}
              />
              <InputGroup.Append>
                <InputGroup.Text id="enrollmentPeriod-unit">
                  days
                </InputGroup.Text>
              </InputGroup.Append>
            </InputGroup>
          </Form.Group>

          <Form.Group as={Col} className="mx-5" controlId="experimentDuration">
            <Form.Label className="d-flex align-items-center">
              Experiment duration
              {isMissingField("proposed_duration") && (
                <InlineErrorIcon
                  name="duration"
                  message="Proposed duration cannot be blank"
                />
              )}
            </Form.Label>
            <InputGroup className="mb-3">
              <Form.Control
                placeholder="28"
                aria-describedby="experimentDuration-unit"
                defaultValue={proposedDuration || 28}
              />
              <InputGroup.Append>
                <InputGroup.Text id="experimentDuration-unit">
                  days
                </InputGroup.Text>
              </InputGroup.Append>
            </InputGroup>
          </Form.Group>
        </Form.Row>
      </Form.Group>

      <div className="d-flex flex-row-reverse bd-highlight">
        <div className="p-2">
          <button data-testid="next-button" className="btn btn-secondary">
            Next
          </button>
        </div>
        <div className="p-2">
          <button
            data-testid="save-button"
            type="submit"
            className="btn btn-primary"
          >
            <span>Save</span>
          </button>
        </div>
      </div>
    </Form>
  );
};

const SelectOptions = ({
  options,
}: {
  options: null | (null | { label: null | string; value: null | string })[];
}) => (
  <>
    <option value="">Select...</option>
    {options?.map(
      (item, idx) =>
        item && (
          <option key={idx} value={item.value || ""}>
            {item.label}
          </option>
        ),
    )}
  </>
);

export default FormAudience;
