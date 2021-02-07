/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useContext } from "react";
import Alert from "react-bootstrap/Alert";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import InputGroup from "react-bootstrap/InputGroup";
import { useCommonForm } from "../../../hooks";
import { useConfig } from "../../../hooks/useConfig";
import { EXTERNAL_URLS, NUMBER_FIELD } from "../../../lib/constants";
import { ExperimentContext } from "../../../lib/contexts";
import InlineErrorIcon from "../../InlineErrorIcon";
import LinkExternal from "../../LinkExternal";

type FormAudienceProps = {
  submitErrors: Record<string, string[]>;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
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
  submitErrors,
  setSubmitErrors,
  isServerValid,
  isLoading,
  onSubmit,
  onNext,
}: FormAudienceProps) => {
  const {
    experiment,
    review: { ready, isMissingField },
  } = useContext(ExperimentContext);
  const {
    channel,
    firefoxMinVersion,
    targetingConfigSlug,
    populationPercent,
    totalEnrolledClients,
    proposedEnrollment,
    proposedDuration,
  } = experiment!;

  const config = useConfig();

  const defaultValues = {
    channel,
    firefoxMinVersion,
    targetingConfigSlug,
    populationPercent,
    totalEnrolledClients,
    proposedEnrollment,
    proposedDuration,
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

  const isNextDisabled = isLoading || ready;

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
              <SelectOptions options={config.channel} />
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
          <LinkExternal
            href={EXTERNAL_URLS.WORKFLOW_MANA_DOC}
            data-testid="learn-more-link"
          >
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
                {...formControlAttrs("populationPercent", NUMBER_FIELD)}
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
              {...formControlAttrs("totalEnrolledClients", NUMBER_FIELD)}
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
                {...formControlAttrs("proposedEnrollment", NUMBER_FIELD)}
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
                {...formControlAttrs("proposedDuration", NUMBER_FIELD)}
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
