/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback } from "react";
import Form from "react-bootstrap/Form";
import Alert from "react-bootstrap/Alert";
import InputGroup from "react-bootstrap/InputGroup";
import Col from "react-bootstrap/Col";
import LinkExternal from "../LinkExternal";
import InlineErrorIcon from "../InlineErrorIcon";
import { useConfig } from "../../hooks/useConfig";

import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { getConfig_nimbusConfig_channel } from "../../types/getConfig";
import { useCommonForm } from "../../hooks";

export const AUDIENCE_DOC_URL =
  "https://mana.mozilla.org/wiki/pages/viewpage.action?pageId=109990007";

type FormAudienceProps = {
  experiment: getExperiment_experimentBySlug;
  submitErrors: Record<string, string[]>;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  isMissingField: (fieldName: string) => boolean;
  isServerValid: boolean;
  isLoading: boolean;
  onSubmit: (data: Record<string, any>, reset: Function) => void;
  onNext?: (ev: React.FormEvent) => void;
};

type AudienceFieldName = typeof audienceFieldNames[number];

export const audienceFieldNames = [
  "channel",
  "firefoxMinVersion",
  "targetingConfigSlug",
  "populationPercent",
  "totalEnrolledClients",
  "proposedEnrollment",
  "proposedDuration",
] as const;

export const FormAudience = ({
  experiment,
  submitErrors,
  setSubmitErrors,
  isMissingField,
  isServerValid,
  isLoading,
  onSubmit,
  onNext,
}: FormAudienceProps) => {
  const config = useConfig();

  // This could be improved on the GraphQL side, but right now in order
  // to filter available channels we need to
  //   - identify the application label by experiment application value
  //   - use that label to identify the available channels
  //   - and then filter all channels against our eligible subset
  const experimentApplication = config.application?.find(
    (a) => a?.value === experiment.application,
  );
  const applicationChannels = config.applicationChannels?.find(
    (ac) => ac?.label === experimentApplication?.label,
  )?.channels;
  const channelOptions = config.channel?.filter(
    (item): item is getConfig_nimbusConfig_channel =>
      item !== null && (applicationChannels?.includes(item.label) || false),
  );

  const defaultValues = {
    channel: experiment.channel,
    firefoxMinVersion: experiment.firefoxMinVersion,
    targetingConfigSlug: experiment.targetingConfigSlug,
    populationPercent: experiment.populationPercent,
    totalEnrolledClients: experiment.totalEnrolledClients,
    proposedEnrollment: experiment.proposedEnrollment,
    proposedDuration: experiment.proposedDuration,
  };

  const {
    FormErrors,
    formControlAttrs,
    isValid,
    handleSubmit,
    reset,
    isSubmitted,
  } = useCommonForm<AudienceFieldName>(
    defaultValues,
    isServerValid,
    submitErrors,
    setSubmitErrors,
  );

  type DefaultValues = typeof defaultValues;

  const handleSubmitAfterValidation = useCallback(
    (dataIn: DefaultValues) => {
      if (isLoading) return;
      onSubmit(dataIn, reset);
    },
    [isLoading, onSubmit, reset],
  );

  const handleNext = useCallback(
    (ev: React.FormEvent) => {
      ev.preventDefault();
      onNext!(ev);
    },
    [onNext],
  );

  const isNextDisabled = isLoading || !experiment?.readyForReview?.ready;

  return (
    <Form
      noValidate
      onSubmit={handleSubmit(handleSubmitAfterValidation)}
      validated={isSubmitted && isValid}
      data-testid="FormAudience"
    >
      {submitErrors["*"] && (
        <Alert data-testid="submit-error" variant="warning">
          {submitErrors["*"]}
        </Alert>
      )}

      <Form.Group>
        <Form.Row>
          <Form.Group as={Col} controlId="channel" md={8} lg={8}>
            <Form.Label className="d-flex align-items-center">
              Channel
              {isMissingField("channel") && (
                <InlineErrorIcon
                  name="channel"
                  message="A channel must be selected"
                />
              )}
            </Form.Label>
            <Form.Control {...formControlAttrs("channel")} as="select">
              <SelectOptions options={channelOptions!} />
            </Form.Control>
            <FormErrors name="channel" />
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
              {...formControlAttrs("firefoxMinVersion")}
              as="select"
            >
              <SelectOptions options={config.firefoxMinVersion} />
            </Form.Control>
            <FormErrors name="firefoxMinVersion" />
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
              {...formControlAttrs("targetingConfigSlug")}
              as="select"
            >
              <SelectOptions options={config.targetingConfigSlug} />
            </Form.Control>
            <FormErrors name="targetingConfigSlug" />
          </Form.Group>
        </Form.Row>
      </Form.Group>

      <Form.Group className="bg-light p-4">
        <p className="text-secondary">
          Please ask a data scientist to help you determine these values.{" "}
          <LinkExternal href={AUDIENCE_DOC_URL} data-testid="learn-more-link">
            Learn more
          </LinkExternal>
        </p>

        <Form.Row>
          <Form.Group as={Col} className="mx-5" controlId="populationPercent">
            <Form.Label>
              Percent of clients
              {isMissingField("population_percent") && (
                <InlineErrorIcon
                  name="population-percent"
                  message="A valid percent of clients must be set"
                />
              )}
            </Form.Label>
            <InputGroup>
              <Form.Control
                {...formControlAttrs("populationPercent")}
                aria-describedby="populationPercent-unit"
                type="number"
                min="0"
                max="100"
                step="0.0001"
              />
              <InputGroup.Append>
                <InputGroup.Text id="populationPercent-unit">%</InputGroup.Text>
              </InputGroup.Append>
              <FormErrors name="populationPercent" />
            </InputGroup>
          </Form.Group>

          <Form.Group
            as={Col}
            className="mx-5"
            controlId="totalEnrolledClients"
          >
            <Form.Label>Expected number of clients</Form.Label>
            <Form.Control
              {...formControlAttrs("totalEnrolledClients")}
              type="number"
              min="0"
            />
            <FormErrors name="totalEnrolledClients" />
          </Form.Group>
        </Form.Row>

        <Form.Row>
          <Form.Group as={Col} className="mx-5" controlId="proposedEnrollment">
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
                {...formControlAttrs("proposedEnrollment")}
                type="number"
                min="0"
                aria-describedby="proposedEnrollment-unit"
              />
              <InputGroup.Append>
                <InputGroup.Text id="proposedEnrollment-unit">
                  days
                </InputGroup.Text>
              </InputGroup.Append>
              <FormErrors name="proposedEnrollment" />
            </InputGroup>
          </Form.Group>

          <Form.Group as={Col} className="mx-5" controlId="proposedDuration">
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
                {...formControlAttrs("proposedDuration")}
                type="number"
                min="0"
                aria-describedby="proposedDuration-unit"
              />
              <InputGroup.Append>
                <InputGroup.Text id="proposedDuration-unit">
                  days
                </InputGroup.Text>
              </InputGroup.Append>
              <FormErrors name="proposedDuration" />
            </InputGroup>
          </Form.Group>
        </Form.Row>
      </Form.Group>

      <div className="d-flex flex-row-reverse bd-highlight">
        <div className="p-2">
          <button
            onClick={handleNext}
            className="btn btn-secondary"
            disabled={isNextDisabled}
            data-testid="next-button"
            data-sb-kind="pages/RequestReview"
          >
            Next
          </button>
        </div>
        <div className="p-2">
          <button
            data-testid="submit-button"
            type="submit"
            onClick={handleSubmit(handleSubmitAfterValidation)}
            className="btn btn-primary"
            disabled={isLoading}
            data-sb-kind="pages/EditOverview"
          >
            <span>{isLoading ? "Saving" : "Save"}</span>
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
