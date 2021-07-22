/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import InputGroup from "react-bootstrap/InputGroup";
import Select from "react-select";
import ReactTooltip from "react-tooltip";
import { useCommonForm, useConfig, useReviewCheck } from "../../../hooks";
import { ReactComponent as Info } from "../../../images/info.svg";
import {
  EXTERNAL_URLS,
  POSITIVE_NUMBER_FIELD,
  POSITIVE_NUMBER_WITH_COMMAS_FIELD,
  TOOLTIP_DURATION,
} from "../../../lib/constants";
import {
  getConfig_nimbusConfig,
  getConfig_nimbusConfig_targetingConfigSlug,
} from "../../../types/getConfig";
import { getExperiment_experimentBySlug } from "../../../types/getExperiment";
import LinkExternal from "../../LinkExternal";

type FormAudienceProps = {
  experiment: getExperiment_experimentBySlug;
  submitErrors: SerializerMessages;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  isServerValid: boolean;
  isLoading: boolean;
  onSubmit: (data: Record<string, any>, next: boolean) => void;
};

type AudienceFieldName = typeof audienceFieldNames[number];
type SelectIdItems = {
  id: number;
  name: string;
}[];

export const audienceFieldNames = [
  "channel",
  "firefoxMinVersion",
  "targetingConfigSlug",
  "populationPercent",
  "totalEnrolledClients",
  "proposedEnrollment",
  "proposedDuration",
  "countries",
  "locales",
] as const;

const selectOptions = (items: SelectIdItems) =>
  items.map((item) => ({
    label: item.name!,
    value: item.id!,
  }));

export const FormAudience = ({
  experiment,
  submitErrors,
  setSubmitErrors,
  isServerValid,
  isLoading,
  onSubmit,
}: FormAudienceProps) => {
  const config = useConfig();
  const { fieldMessages } = useReviewCheck(experiment);

  const [locales, setLocales] = useState<string[]>(
    experiment!.locales.map((v) => "" + v.id!),
  );
  const [countries, setCountries] = useState<string[]>(
    experiment!.countries.map((v) => "" + v.id!),
  );

  const defaultValues = {
    channel: experiment.channel,
    firefoxMinVersion: experiment.firefoxMinVersion,
    targetingConfigSlug: experiment.targetingConfigSlug,
    populationPercent: experiment.populationPercent,
    totalEnrolledClients: experiment.totalEnrolledClients,
    proposedEnrollment: experiment.proposedEnrollment,
    proposedDuration: experiment.proposedDuration,
    countries: selectOptions(experiment.countries as SelectIdItems),
    locales: selectOptions(experiment.locales as SelectIdItems),
  };

  const {
    FormErrors,
    formControlAttrs,
    formSelectAttrs,
    isValid,
    handleSubmit,
    isSubmitted,
  } = useCommonForm<AudienceFieldName>(
    defaultValues,
    isServerValid,
    submitErrors,
    setSubmitErrors,
    fieldMessages,
  );

  type DefaultValues = typeof defaultValues;
  const [handleSave, handleSaveNext] = useMemo(
    () =>
      [false, true].map((next) =>
        handleSubmit(
          (dataIn: DefaultValues) =>
            !isLoading &&
            onSubmit(
              {
                ...dataIn,
                locales,
                countries,
              },
              next,
            ),
        ),
      ),
    [isLoading, onSubmit, handleSubmit, locales, countries],
  );

  const targetingConfigSlugOptions = useMemo(
    () =>
      filterTargetingConfigSlug(
        config.targetingConfigSlug,
        experiment.application,
      ),
    [config, experiment],
  );

  return (
    <Form
      noValidate
      onSubmit={handleSave}
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
          <Form.Group as={Col} controlId="channel">
            <Form.Label className="d-flex align-items-center">
              Channel
            </Form.Label>
            <Form.Control {...formControlAttrs("channel")} as="select">
              <SelectOptions options={config.channel} />
            </Form.Control>
            <FormErrors name="channel" />
          </Form.Group>
          <Form.Group as={Col} controlId="minVersion">
            <Form.Label className="d-flex align-items-center">
              Min Version
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
          <Form.Group as={Col} controlId="locales" data-testid="locales">
            <Form.Label>Locales</Form.Label>
            <Select
              placeholder="All Locales"
              isMulti
              {...formSelectAttrs("locales", setLocales)}
              options={selectOptions(config.locales as SelectIdItems)}
            />
            <FormErrors name="locales" />
          </Form.Group>
          <Form.Group as={Col} controlId="countries" data-testid="countries">
            <Form.Label>Countries</Form.Label>
            <Select
              placeholder="All Countries"
              isMulti
              {...formSelectAttrs("countries", setCountries)}
              options={selectOptions(config.countries as SelectIdItems)}
            />
            <FormErrors name="countries" />
          </Form.Group>
        </Form.Row>
        <Form.Row>
          <Form.Group as={Col} controlId="targeting">
            <Form.Label className="d-flex align-items-center">
              Advanced Targeting
            </Form.Label>
            <Form.Control
              {...formControlAttrs("targetingConfigSlug")}
              as="select"
            >
              <SelectOptions options={targetingConfigSlugOptions} />
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
            <Form.Label>Percent of clients</Form.Label>
            <InputGroup>
              <Form.Control
                {...formControlAttrs(
                  "populationPercent",
                  POSITIVE_NUMBER_FIELD,
                )}
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
              {...formControlAttrs(
                "totalEnrolledClients",
                POSITIVE_NUMBER_WITH_COMMAS_FIELD,
              )}
            />
            <FormErrors name="totalEnrolledClients" />
          </Form.Group>
        </Form.Row>

        <Form.Row>
          <Form.Group as={Col} className="mx-5" controlId="proposedEnrollment">
            <Form.Label className="d-flex align-items-center">
              Enrollment period
            </Form.Label>
            <InputGroup>
              <Form.Control
                {...formControlAttrs(
                  "proposedEnrollment",
                  POSITIVE_NUMBER_FIELD,
                )}
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
              <Info
                data-tip={TOOLTIP_DURATION}
                data-testid="tooltip-duration-audience"
                width="20"
                height="20"
                className="ml-1"
              />
              <ReactTooltip />
            </Form.Label>
            <InputGroup className="mb-3">
              <Form.Control
                {...formControlAttrs("proposedDuration", POSITIVE_NUMBER_FIELD)}
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
            onClick={handleSaveNext}
            className="btn btn-secondary"
            id="save-and-continue-button"
            disabled={isLoading}
            data-testid="next-button"
            data-sb-kind="pages/Summary"
          >
            Save and Continue
          </button>
        </div>
        <div className="p-2">
          <button
            data-testid="submit-button"
            type="submit"
            onClick={handleSave}
            className="btn btn-primary"
            id="save-button"
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

export const filterTargetingConfigSlug = (
  targetingConfigs: getConfig_nimbusConfig["targetingConfigSlug"],
  application: getExperiment_experimentBySlug["application"],
) =>
  targetingConfigs == null
    ? []
    : targetingConfigs.filter(
        (
          targetingConfig,
        ): targetingConfig is getConfig_nimbusConfig_targetingConfigSlug =>
          targetingConfig !== null &&
          Array.isArray(targetingConfig.applicationValues) &&
          targetingConfig.applicationValues.includes(application),
      );

export default FormAudience;
