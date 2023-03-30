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
import LinkExternal from "src/components/LinkExternal";
import { useCommonForm, useConfig, useReviewCheck } from "src/hooks";
import { ReactComponent as Info } from "src/images/info.svg";
import {
  EXTERNAL_URLS,
  POSITIVE_NUMBER_FIELD,
  POSITIVE_NUMBER_WITH_COMMAS_FIELD,
  TOOLTIP_DURATION,
} from "src/lib/constants";
import { getStatus } from "src/lib/experiment";
import {
  getConfig_nimbusConfig,
  getConfig_nimbusConfig_targetingConfigs,
} from "src/types/getConfig";
import { getExperiment_experimentBySlug } from "src/types/getExperiment";
import { NimbusExperimentApplicationEnum } from "src/types/globalTypes";

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
  id: string;
  name: string;
}[];

export const audienceFieldNames = [
  "channel",
  "firefoxMinVersion",
  "firefoxMaxVersion",
  "targetingConfigSlug",
  "populationPercent",
  "totalEnrolledClients",
  "proposedEnrollment",
  "proposedDuration",
  "countries",
  "locales",
  "languages",
  "isSticky",
  "isFirstRun",
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
  const { fieldMessages, fieldWarnings } = useReviewCheck(experiment);

  const [locales, setLocales] = useState<string[]>(
    experiment!.locales.map((v) => "" + v.id!),
  );
  const [countries, setCountries] = useState<string[]>(
    experiment!.countries.map((v) => "" + v.id!),
  );
  const [languages, setLanguages] = useState<string[]>(
    experiment!.languages.map((v) => "" + v.id!),
  );

  const [isSticky, setIsSticky] = useState<boolean>(
    experiment.isSticky ?? false,
  );

  const [isFirstRun, setIsFirstRun] = useState<boolean>(
    experiment.isFirstRun ?? false,
  );
  const [stickyRequiredWarning, setStickyRequiredWarning] = useState<boolean>(
    experiment.targetingConfig![0]?.stickyRequired ?? false,
  );
  const [isFirstRunRequiredWarning, setisFirstRunRequiredRequiredWarning] =
    useState<boolean>(
      experiment.targetingConfig![0]?.isFirstRunRequired ?? false,
    );

  const applicationConfig = config.applicationConfigs?.find(
    (applicationConfig) =>
      applicationConfig?.application === experiment.application,
  );

  const [populationPercent, setPopulationPercent] = useState(
    experiment!.populationPercent?.toString(),
  );

  const defaultValues = {
    channel: experiment.channel,
    firefoxMinVersion: experiment.firefoxMinVersion,
    firefoxMaxVersion: experiment.firefoxMaxVersion,
    targetingConfigSlug: experiment.targetingConfigSlug,
    populationPercent: experiment.populationPercent,
    totalEnrolledClients: experiment.totalEnrolledClients,
    proposedEnrollment: experiment.proposedEnrollment,
    proposedDuration: experiment.proposedDuration,
    countries: selectOptions(experiment.countries as SelectIdItems),
    locales: selectOptions(experiment.locales as SelectIdItems),
    languages: selectOptions(experiment.languages as SelectIdItems),
    isSticky: experiment.isSticky,
    isFirstRun: experiment.isFirstRun,
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
    fieldWarnings,
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
                isSticky,
                populationPercent,
                isFirstRun,
                locales,
                countries,
                languages,
              },
              next,
            ),
        ),
      ),
    [
      isLoading,
      onSubmit,
      handleSubmit,
      isSticky,
      populationPercent,
      isFirstRun,
      locales,
      countries,
      languages,
    ],
  );

  const targetingConfigSlugOptions = useMemo(
    () =>
      filterAndSortTargetingConfigs(
        config.targetingConfigs,
        experiment.application,
      ),
    [config, experiment],
  );

  const TargetingOnChange = (ev: React.ChangeEvent<HTMLInputElement>) => {
    const checkRequired = targetingConfigSlugOptions.find(
      (config) => config.value === ev.target.value,
    );
    setIsSticky(checkRequired?.stickyRequired || false);
    setStickyRequiredWarning(!!checkRequired?.stickyRequired);
    setIsFirstRun(
      checkRequired?.isFirstRunRequired || experiment.isFirstRun || false,
    );
    setisFirstRunRequiredRequiredWarning(!!checkRequired?.isFirstRunRequired);
    setPopulationPercent(populationPercent);
  };

  const isDesktop =
    experiment.application === NimbusExperimentApplicationEnum.DESKTOP;
  const isLiveRollout = experiment.isRollout && getStatus(experiment).live;
  const isLocked = isLiveRollout && !getStatus(experiment).draft;

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
            <Form.Control
              {...formControlAttrs("channel")}
              as="select"
              disabled={isLocked!}
              custom
            >
              <SelectOptions options={applicationConfig!.channels!} />
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
              disabled={isLocked!}
              custom
            >
              <SelectOptions options={config.firefoxVersions} />
            </Form.Control>
            <FormErrors name="firefoxMinVersion" />
          </Form.Group>
          <Form.Group as={Col} controlId="maxVersion">
            <Form.Label className="d-flex align-items-center">
              Max Version
            </Form.Label>
            <Form.Control
              {...formControlAttrs("firefoxMaxVersion")}
              as="select"
              disabled={isLocked!}
              custom
            >
              <SelectOptions options={config.firefoxVersions} />
            </Form.Control>
            <FormErrors name="firefoxMaxVersion" />
          </Form.Group>
        </Form.Row>
        <Form.Row>
          {isDesktop && (
            <Form.Group as={Col} controlId="locales" data-testid="locales">
              <Form.Label>Locales</Form.Label>
              <Select
                placeholder="All Locales"
                isMulti
                {...formSelectAttrs("locales", setLocales)}
                options={selectOptions(config.locales as SelectIdItems)}
                isDisabled={isLocked!}
              />
              <FormErrors name="locales" />
            </Form.Group>
          )}
          {!isDesktop && (
            <Form.Group as={Col} controlId="languages" data-testid="languages">
              <Form.Label>Languages</Form.Label>
              <Select
                placeholder="All Languages"
                isMulti
                {...formSelectAttrs("languages", setLanguages)}
                options={selectOptions(config.languages as SelectIdItems)}
                isDisabled={isLocked!}
              />
              <FormErrors name="languages" />
            </Form.Group>
          )}
          <Form.Group as={Col} controlId="countries" data-testid="countries">
            <Form.Label>Countries</Form.Label>
            <Select
              placeholder="All Countries"
              isMulti
              {...formSelectAttrs("countries", setCountries)}
              options={selectOptions(config.countries as SelectIdItems)}
              isDisabled={isLocked!}
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
              onChange={TargetingOnChange.bind(this)}
              disabled={isLocked!}
              custom
            >
              <TargetConfigSelectOptions options={targetingConfigSlugOptions} />
            </Form.Control>
            <FormErrors name="targetingConfigSlug" />
          </Form.Group>
        </Form.Row>
        <Form.Row>
          <Form.Group as={Col} controlId="isSticky">
            <Form.Label>
              <Form.Check
                {...formControlAttrs("isSticky")}
                type="checkbox"
                checked={isSticky}
                onChange={(e) => setIsSticky(e.target.checked)}
                disabled={stickyRequiredWarning || isLocked!}
                label="Sticky Enrollment (Clients remain enrolled until the experiment ends)"
              />
            </Form.Label>
            <LinkExternal
              href={EXTERNAL_URLS.CUSTOM_AUDIENCES_EXPLANATION}
              className="ml-1"
            >
              Learn more
            </LinkExternal>
            {stickyRequiredWarning && (
              <Alert data-testid="sticky-required-warning" variant="warning">
                Sticky enrollment is required for this targeting configuration.
              </Alert>
            )}
            <FormErrors name="isSticky" />
          </Form.Group>
        </Form.Row>
        {!isDesktop && (
          <Form.Row>
            <Form.Group as={Col} controlId="isFirstRun">
              <Form.Check
                {...formControlAttrs("isFirstRun")}
                type="checkbox"
                onChange={(e) => setIsFirstRun(e.target.checked)}
                checked={isFirstRun}
                disabled={isFirstRunRequiredWarning || isLocked!}
                label="First Run Experiment"
              />
              {isFirstRunRequiredWarning && (
                <Alert
                  data-testid="is-first-run-required-warning"
                  variant="warning"
                >
                  First run is required for this targeting configuration.
                </Alert>
              )}
              <FormErrors name="isFirstRun" />
            </Form.Group>
          </Form.Row>
        )}
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

        <Form.Row data-testid="population-percent-top-row">
          <Form.Group
            as={Col}
            className="mt-2 mb-0"
            controlId="populationPercent"
            data-testid="population-percent-top"
          >
            <InputGroup className="mx-0 d-flex">
              <Form.Label
                style={{
                  display: "inline-block",
                  marginBottom: 0,
                }}
              >
                Percent of clients
              </Form.Label>
            </InputGroup>
            <InputGroup>
              <Form.Control
                {...formControlAttrs("populationPercent")}
                type="hidden"
                value={populationPercent}
              />
              <Form.Control
                aria-describedby="populationPercent-unit"
                type="range"
                min="0"
                max="100"
                step="5"
                className="pb-4"
                value={populationPercent}
                onChange={(e) => setPopulationPercent(e.target.value)}
                data-testid="population-percent-slider"
                disabled={isLocked! && !isLiveRollout}
              />
              <Form.Control
                aria-describedby="populationPercent-unit"
                defaultValue={"0"}
                value={populationPercent}
                onChange={(e) => setPopulationPercent(e.target.value)}
                data-testid="population-percent-text"
                disabled={isLocked! && !isLiveRollout}
              />
              <InputGroup.Append>
                <InputGroup.Text id="populationPercent-unit">%</InputGroup.Text>
              </InputGroup.Append>
              <FormErrors name="populationPercent" />
            </InputGroup>
          </Form.Group>

          <Form.Group
            as={Col}
            className="mx-5 pt-4"
            controlId="totalEnrolledClients"
          >
            <Form.Label className="mb-2 mt-3">
              Expected number of clients
            </Form.Label>
            <Form.Control
              {...formControlAttrs(
                "totalEnrolledClients",
                POSITIVE_NUMBER_WITH_COMMAS_FIELD,
              )}
              disabled={isLocked!}
            />
            <FormErrors name="totalEnrolledClients" />
          </Form.Group>
        </Form.Row>

        <Form.Row>
          <Form.Group as={Col} className="mt-2" controlId="proposedEnrollment">
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
                disabled={isLocked!}
              />
              <InputGroup.Append>
                <InputGroup.Text id="proposedEnrollment-unit">
                  days
                </InputGroup.Text>
              </InputGroup.Append>
              <FormErrors name="proposedEnrollment" />
            </InputGroup>
          </Form.Group>

          <Form.Group
            as={Col}
            className="mx-5 pt-2"
            controlId="proposedDuration"
          >
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
                disabled={isLocked!}
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
            disabled={isLoading || (isLocked! && !isLiveRollout)}
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
            disabled={isLoading || (isLocked! && !isLiveRollout)}
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
  options:
    | null
    | (null | {
        label: null | string;
        value: null | string;
      })[];
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
const TargetConfigSelectOptions = ({
  options,
}: {
  options:
    | null
    | (null | {
        label: null | string;
        value: null | string;
        description: null | string;
      })[];
}) => (
  <>
    {options?.map(
      (item, idx) =>
        item && (
          <option key={idx} value={item.value || ""}>
            {item.label}
            {item.description?.length ? ` - ${item.description}` : ""}
          </option>
        ),
    )}
  </>
);

export const filterAndSortTargetingConfigs = (
  targetingConfigs: getConfig_nimbusConfig["targetingConfigs"],
  application: getExperiment_experimentBySlug["application"],
) =>
  targetingConfigs == null
    ? []
    : targetingConfigs
        .filter(
          (
            targetingConfig,
          ): targetingConfig is getConfig_nimbusConfig_targetingConfigs =>
            targetingConfig !== null &&
            Array.isArray(targetingConfig.applicationValues) &&
            targetingConfig.applicationValues.includes(application),
        )
        .sort(
          // sort with default value '' first, then alphabetical
          (a, b): number =>
            Number(b?.value === "") - Number(a?.value === "") ||
            a?.label?.localeCompare(b?.label || "") ||
            0,
        );

export default FormAudience;
