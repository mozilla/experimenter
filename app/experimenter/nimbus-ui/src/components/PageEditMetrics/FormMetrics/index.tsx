/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useEffect, useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";
import Select from "react-select";
import ReactTooltip from "react-tooltip";
import { useCommonForm, useConfig, useExitWarning } from "../../../hooks";
import { SelectOption } from "../../../hooks/useCommonForm/useCommonFormMethods";
import { useOutcomes } from "../../../hooks/useOutcomes";
import { ReactComponent as Info } from "../../../images/info.svg";
import { getConfig_nimbusConfig_outcomes } from "../../../types/getConfig";
import { getExperiment } from "../../../types/getExperiment";

export const metricsFieldNames = [
  "primaryOutcomeSlugs",
  "secondaryOutcomeSlugs",
] as const;

type FormMetricsProps = {
  experiment: getExperiment["experimentBySlug"];
  isLoading: boolean;
  isServerValid: boolean;
  submitErrors: Record<string, string[]>;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  onSave: (data: Record<string, any>, next: boolean) => void;
};

type MetricsFieldName = typeof metricsFieldNames[number];

export const PRIMARY_OUTCOMES_TOOLTIP =
  "Specific metrics you’d like to impact in your experiment, which will be part of the analysis.";
export const SECONDARY_OUTCOMES_TOOLTIP =
  "Specific metrics that you are interested in observing in your experiment but they don't affect the results of your experiment.";

const FormMetrics = ({
  experiment,
  isLoading,
  isServerValid,
  submitErrors,
  setSubmitErrors,
  onSave,
}: FormMetricsProps) => {
  const { outcomes: configOutcomes } = useConfig();
  const { primaryOutcomes, secondaryOutcomes } = useOutcomes(experiment!);

  // We must alter primary outcome options when a secondary set is selected
  // to exclude the set from primary outcome options and vice versa
  const [primaryOutcomeSlugs, setPrimaryOutcomeSlugs] = useState<string[]>(
    experiment!.primaryOutcomes as string[],
  );
  const [secondaryOutcomeSlugs, setSecondaryOutcomeSlugs] = useState<string[]>(
    experiment!.secondaryOutcomes as string[],
  );

  const outcomeOption = (outcome: getConfig_nimbusConfig_outcomes) => ({
    label: outcome.friendlyName!,
    value: outcome.slug!,
  });

  const primaryOutcomeOptions: SelectOption[] = [];
  const secondaryOutcomeOptions: SelectOption[] = [];

  // Get primary/secondary options from server-supplied array of outcomes
  configOutcomes?.forEach((outcome) => {
    if (!secondaryOutcomeSlugs.includes(outcome!.slug as string)) {
      primaryOutcomeOptions.push(outcomeOption(outcome!));
    }
    if (!primaryOutcomeSlugs.includes(outcome!.slug as string)) {
      secondaryOutcomeOptions.push(outcomeOption(outcome!));
    }
  });

  const defaultValues = {
    primaryOutcomeSlugs: primaryOutcomes.map((outcome) =>
      outcomeOption(outcome),
    ),
    secondaryOutcomeSlugs: secondaryOutcomes.map((outcome) =>
      outcomeOption(outcome),
    ),
  };

  const {
    FormErrors,
    formSelectAttrs,
    isValid,
    isDirtyUnsaved,
    handleSubmit,
    isSubmitted,
  } = useCommonForm<MetricsFieldName>(
    defaultValues,
    isServerValid,
    submitErrors,
    setSubmitErrors,
  );

  const shouldWarnOnExit = useExitWarning();
  useEffect(() => {
    shouldWarnOnExit(isDirtyUnsaved);
  }, [shouldWarnOnExit, isDirtyUnsaved]);

  const [handleSave, handleSaveNext] = useMemo(
    () =>
      [false, true].map((next) =>
        handleSubmit(() => {
          console.log("hey?", primaryOutcomeSlugs, secondaryOutcomeSlugs);
          !isLoading &&
            onSave(
              {
                primaryOutcomeSlugs,
                secondaryOutcomeSlugs,
              },
              next,
            );
        }),
      ),
    [
      isLoading,
      onSave,
      handleSubmit,
      primaryOutcomeSlugs,
      secondaryOutcomeSlugs,
    ],
  );

  return (
    <Form
      noValidate
      onSubmit={handleSave}
      validated={isSubmitted && isValid}
      data-testid="FormMetrics"
    >
      {submitErrors["*"] && (
        <Alert data-testid="submit-error" variant="warning">
          {submitErrors["*"]}
        </Alert>
      )}

      <Form.Group
        controlId="primaryOutcomeSlugs"
        data-testid="primary-outcomes"
      >
        <Form.Label>
          Primary Outcomes{" "}
          <Info
            data-tip={PRIMARY_OUTCOMES_TOOLTIP}
            data-testid="tooltip-primary-outcomes"
            width="20"
            height="20"
            className="ml-1"
          />
          <ReactTooltip />
        </Form.Label>
        <Select
          isMulti
          {...formSelectAttrs("primaryOutcomeSlugs", setPrimaryOutcomeSlugs)}
          options={primaryOutcomeOptions}
          isOptionDisabled={() => primaryOutcomeSlugs.length >= 2}
        />
        <Form.Text className="text-muted">
          Select the user action or feature that you are measuring with this
          experiment. You may select up to 2 primary outcomes.
        </Form.Text>
        <FormErrors name="primaryOutcomeSlugs" />
      </Form.Group>

      <Form.Group
        controlId="secondaryOutcomeSlugs"
        data-testid="secondary-outcomes"
      >
        <Form.Label>
          Secondary Outcomes{" "}
          <Info
            data-tip={SECONDARY_OUTCOMES_TOOLTIP}
            data-testid="tooltip-secondary-outcomes"
            width="20"
            height="20"
            className="ml-1"
          />
        </Form.Label>
        <Select
          isMulti
          {...formSelectAttrs(
            "secondaryOutcomeSlugs",
            setSecondaryOutcomeSlugs,
          )}
          options={secondaryOutcomeOptions}
        />
        <Form.Text className="text-muted">
          Select the user action or feature that you are measuring with this
          experiment.
        </Form.Text>
        <FormErrors name="secondaryOutcomeSlugs" />
      </Form.Group>

      <div className="d-flex flex-row-reverse bd-highlight">
        <div className="p-2">
          <button
            onClick={handleSaveNext}
            data-testid="next-button"
            className="btn btn-secondary"
            disabled={isLoading}
            data-sb-kind="pages/EditMetrics"
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
            disabled={isLoading}
            data-sb-kind="pages/EditMetrics"
          >
            {isLoading ? <span>Saving</span> : <span>Save</span>}
          </button>
        </div>
      </div>
    </Form>
  );
};

export default FormMetrics;
