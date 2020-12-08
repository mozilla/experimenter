/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback } from "react";
import {
  useForm,
  Controller,
  ValidationRules,
  FieldError,
} from "react-hook-form";
import Select from "react-select";
import Form from "react-bootstrap/Form";
import Alert from "react-bootstrap/Alert";
import InputGroup from "react-bootstrap/InputGroup";
import Col from "react-bootstrap/Col";
import LinkExternal from "../LinkExternal";
import InlineErrorIcon from "../InlineErrorIcon";
import { useConfig } from "../../hooks/useConfig";

import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import { getConfig_nimbusConfig_channels } from "../../types/getConfig";

// TODO: find this doco URL
const AUDIENCE_DOC_URL =
  "https://mana.mozilla.org/wiki/pages/viewpage.action?spaceKey=FJT&title=Project+Nimbus";

export const FormAudience = ({
  experiment,
  submitErrors,
  isMissingField,
  isLoading,
  onSubmit,
  onNext,
}: {
  experiment: getExperiment_experimentBySlug;
  submitErrors: Record<string, string[]>;
  isMissingField: (fieldName: string) => boolean;
  isLoading: boolean;
  onSubmit: (data: Record<string, any>, reset: Function) => void;
  onNext?: (ev: React.FormEvent) => void;
}) => {
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
  const channelsOptions = config.channels?.filter(
    (item): item is getConfig_nimbusConfig_channels =>
      item !== null && (applicationChannels?.includes(item.label) || false),
  );
  const channelsDefaultValue = experiment.channels?.map((channel) =>
    channelsOptions?.find((option) => option?.value === channel),
  );

  const defaultValues = {
    channels: channelsDefaultValue,
    firefoxMinVersion: experiment.firefoxMinVersion || "",
    targetingConfigSlug: experiment.targetingConfigSlug || "",
    populationPercent: experiment.populationPercent || 0,
    totalEnrolledClients: experiment.totalEnrolledClients,
    proposedEnrollment: experiment.proposedEnrollment || 7,
    proposedDuration: experiment.proposedDuration || 28,
  };

  const {
    handleSubmit,
    register,
    control,
    reset,
    errors,
    formState: { isValid, isSubmitted, touched },
  } = useForm({
    mode: "onTouched",
    defaultValues,
  });

  type DefaultValues = typeof defaultValues;
  type DefaultValuesKey = keyof DefaultValues;

  const handleSubmitAfterValidation = useCallback(
    (dataIn: DefaultValues) => {
      if (isLoading) return;
      onSubmit(
        {
          ...dataIn,
          channels: dataIn.channels?.map((item) => item?.value),
        },
        reset,
      );
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

  const fieldValidity = <K extends DefaultValuesKey>(name: K) => ({
    isInvalid: Boolean(submitErrors[name] || (touched[name] && errors[name])),
    isValid: Boolean(!submitErrors[name] && touched[name] && !errors[name]),
  });

  const formControlCommon = <K extends DefaultValuesKey>(
    name: K,
    validateRules: ValidationRules = {
      required: "This field may not be blank.",
    },
  ) => ({
    name,
    "data-testid": name,
    ref: register(validateRules),
    defaultValue: defaultValues[name],
    ...fieldValidity(name),
  });

  const FormErrors = <K extends DefaultValuesKey>({ name }: { name: K }) => (
    <>
      {errors[name] && (
        <Form.Control.Feedback type="invalid" data-for={name}>
          {(errors[name] as FieldError).message}
        </Form.Control.Feedback>
      )}
      {submitErrors[name] && (
        <Form.Control.Feedback type="invalid" data-for={name}>
          {submitErrors[name]}
        </Form.Control.Feedback>
      )}
    </>
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
          <Form.Group as={Col} controlId="channels" md={8} lg={8}>
            <Form.Label className="d-flex align-items-center">
              Channels
              {isMissingField("channels") && (
                <InlineErrorIcon
                  name="channels"
                  message="At least one channel must be selected"
                />
              )}
            </Form.Label>
            <Controller
              as={Select}
              control={control}
              isMulti
              inputId="channels"
              name="channels"
              data-testid="channels"
              options={channelsOptions}
              className={
                fieldValidity("channels").isInvalid ? "is-invalid" : ""
              }
              rules={{
                validate: {
                  atLeastOne: (value) =>
                    (Array.isArray(value) && value.length > 0) ||
                    "At least one channel must be selected",
                },
              }}
            />
            <FormErrors name="channels" />
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
              {...formControlCommon("firefoxMinVersion")}
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
              {...formControlCommon("targetingConfigSlug")}
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
          <LinkExternal href={AUDIENCE_DOC_URL}>Learn more</LinkExternal>
        </p>

        <Form.Row>
          <Form.Group as={Col} className="mx-5" controlId="populationPercent">
            <Form.Label>Percent of clients</Form.Label>
            <InputGroup>
              <Form.Control
                {...formControlCommon("populationPercent")}
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
              {...formControlCommon("totalEnrolledClients")}
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
                {...formControlCommon("proposedEnrollment")}
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
                {...formControlCommon("proposedDuration")}
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
