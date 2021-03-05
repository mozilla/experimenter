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
import { ReactComponent as Info } from "../../../images/info.svg";
import { getExperiment } from "../../../types/getExperiment";

export const metricsFieldNames = [
  "primaryOutcomes",
  "secondaryOutcomes",
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

type Outcome = string | null;
type Outcomes = Outcome[] | null;

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
  const { outcomes } = useConfig();

  // We must alter primary outcome options when a secondary outcome is selected
  // to exclude the set from primary outcome options and vice versa
  const [primaryOutcomes, setPrimaryOutcomes] = useState<Outcomes>(
    experiment?.primaryOutcomes! || [],
  );
  const [secondaryOutcomes, setSecondaryOutcomes] = useState<Outcomes>(
    experiment?.secondaryOutcomes! || [],
  );

  const outcomesOption = (outcome: Outcome) => ({
    label: outcome,
    value: outcome,
  });

  const primaryOutcomesOptions: SelectOption[] = [];
  const secondaryOutcomesOptions: SelectOption[] = [];

  // Get primary/secondary options from server-supplied array of probe sets
  outcomes?.forEach((outcome) => {
    if (!secondaryOutcomes?.includes(outcome!.friendlyName)) {
      primaryOutcomesOptions.push(outcomesOption(outcome!));
    }
    if (!primaryOutcomes?.includes(outcome!.slug)) {
      secondaryOutcomesOptions.push(outcomesOption(outcome!));
    }
  });

  const defaultValues = {
    primaryOutcomes:
      experiment?.primaryOutcomes?.map((probeSet) =>
        outcomesOption(probeSet!),
      ) || "",
    secondaryOutcomes:
      experiment?.secondaryOutcomes?.map((probeSet) =>
        outcomesOption(probeSet!),
      ) || "",
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
        handleSubmit(
          () =>
            !isLoading &&
            onSave(
              {
                primaryOutcomes,
                secondaryOutcomes,
              },
              next,
            ),
        ),
      ),
    [isLoading, onSave, handleSubmit, primaryOutcomes, secondaryOutcomes],
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

      <Form.Group controlId="primaryOutcomes" data-testid="primary-probe-sets">
        <Form.Label>
          Primary Probe sets{" "}
          <Info
            data-tip={PRIMARY_OUTCOMES_TOOLTIP}
            data-testid="tooltip-primary-probe-sets"
            width="20"
            height="20"
            className="ml-1"
          />
          <ReactTooltip />
        </Form.Label>
        <Select
          isMulti
          {...formSelectAttrs("primaryOutcomes", setPrimaryOutcomes)}
          options={primaryOutcomesOptions}
          isOptionDisabled={() => primaryOutcomes.length >= 2}
        />
        <Form.Text className="text-muted">
          Select the user action or feature that you are measuring with this
          experiment. You may select up to 2 primary probe sets.
        </Form.Text>
        <FormErrors name="primaryOutcomes" />
      </Form.Group>

      <Form.Group
        controlId="secondaryOutcomes"
        data-testid="secondary-probe-sets"
      >
        <Form.Label>
          Secondary Probe sets{" "}
          <Info
            data-tip={SECONDARY_OUTCOMES_TOOLTIP}
            data-testid="tooltip-secondary-probe-sets"
            width="20"
            height="20"
            className="ml-1"
          />
        </Form.Label>
        <Select
          isMulti
          {...formSelectAttrs("secondaryOutcomes", setSecondaryOutcomes)}
          options={secondaryOutcomesOptions}
        />
        <Form.Text className="text-muted">
          Select the user action or feature that you are measuring with this
          experiment.
        </Form.Text>
        <FormErrors name="secondaryOutcomes" />
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
