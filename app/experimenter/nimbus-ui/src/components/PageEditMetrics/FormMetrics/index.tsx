/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useEffect, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";
import Select from "react-select";
import ReactTooltip from "react-tooltip";
import { useCommonForm, useConfig, useExitWarning } from "../../../hooks";
import { SelectOption } from "../../../hooks/useCommonForm/useCommonFormMethods";
import { ReactComponent as Info } from "../../../images/info.svg";
import {
  getExperiment,
  getExperiment_experimentBySlug_primaryProbeSets,
  getExperiment_experimentBySlug_secondaryProbeSets,
} from "../../../types/getExperiment";

export const metricsFieldNames = [
  "primaryProbeSetIds",
  "secondaryProbeSetIds",
] as const;

type FormMetricsProps = {
  experiment: getExperiment["experimentBySlug"];
  isLoading: boolean;
  isServerValid: boolean;
  submitErrors: Record<string, string[]>;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  onSave: (data: Record<string, any>, reset: Function) => void;
  onNext: (ev: React.FormEvent) => void;
};

type ProbeSet =
  | getExperiment_experimentBySlug_primaryProbeSets
  | getExperiment_experimentBySlug_secondaryProbeSets;

type ProbeSets =
  | (getExperiment_experimentBySlug_primaryProbeSets | null)[]
  | (getExperiment_experimentBySlug_secondaryProbeSets | null)[];

type MetricsFieldName = typeof metricsFieldNames[number];

export const PRIMARY_PROBE_SETS_TOOLTIP =
  "Specific metrics you’d like to impact in your experiment, which will be part of the analysis.";
export const SECONDARY_PROBE_SETS_TOOLTIP =
  "Specific metrics that you are interested in observing in your experiment but they don't affect the results of your experiment.";

const FormMetrics = ({
  experiment,
  isLoading,
  isServerValid,
  submitErrors,
  setSubmitErrors,
  onSave,
  onNext,
}: FormMetricsProps) => {
  const { probeSets } = useConfig();

  const getProbeSetIds = (probeSets: ProbeSets) =>
    probeSets?.map((probeSet) => probeSet?.id as string) || [];

  // We must alter primary probe set options when a secondary set is selected
  // to exclude the set from primary probe set options and vice versa
  const [primaryProbeSetIds, setPrimaryProbeSetIds] = useState<string[]>(
    getProbeSetIds(experiment?.primaryProbeSets!),
  );
  const [secondaryProbeSetIds, setSecondaryProbeSetIds] = useState<string[]>(
    getProbeSetIds(experiment?.secondaryProbeSets!),
  );

  const probeSetOption = (probeSet: ProbeSet) => ({
    label: probeSet.name,
    value: probeSet.id,
  });

  const primaryProbeSetOptions: SelectOption[] = [];
  const secondaryProbeSetOptions: SelectOption[] = [];

  // Get primary/secondary options from server-supplied array of probe sets
  probeSets?.forEach((probeSet) => {
    if (!secondaryProbeSetIds.includes(probeSet!.id)) {
      primaryProbeSetOptions.push(probeSetOption(probeSet!));
    }
    if (!primaryProbeSetIds.includes(probeSet!.id)) {
      secondaryProbeSetOptions.push(probeSetOption(probeSet!));
    }
  });

  const defaultValues = {
    primaryProbeSetIds:
      experiment?.primaryProbeSets?.map((probeSet) =>
        probeSetOption(probeSet!),
      ) || "",
    secondaryProbeSetIds:
      experiment?.secondaryProbeSets?.map((probeSet) =>
        probeSetOption(probeSet!),
      ) || "",
  };

  const {
    FormErrors,
    formSelectAttrs,
    isValid,
    isDirtyUnsaved,
    handleSubmit,
    reset,
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

  const handleSubmitAfterValidation = useCallback(() => {
    if (isLoading) return;
    onSave(
      {
        primaryProbeSetIds,
        secondaryProbeSetIds,
      },
      reset,
    );
  }, [isLoading, onSave, reset, primaryProbeSetIds, secondaryProbeSetIds]);

  const handleNext = useCallback(
    (ev: React.FormEvent) => {
      ev.preventDefault();
      onNext!(ev);
    },
    [onNext],
  );

  return (
    <Form
      noValidate
      onSubmit={handleSubmit(handleSubmitAfterValidation)}
      validated={isSubmitted && isValid}
      data-testid="FormMetrics"
    >
      {submitErrors["*"] && (
        <Alert data-testid="submit-error" variant="warning">
          {submitErrors["*"]}
        </Alert>
      )}

      <Form.Group
        controlId="primaryProbeSetIds"
        data-testid="primary-probe-sets"
      >
        <Form.Label>
          Primary Probe sets{" "}
          <Info
            data-tip={PRIMARY_PROBE_SETS_TOOLTIP}
            data-testid="tooltip-primary-probe-sets"
            width="20"
            height="20"
            className="ml-1"
          />
          <ReactTooltip />
        </Form.Label>
        <Select
          isMulti
          {...formSelectAttrs("primaryProbeSetIds", setPrimaryProbeSetIds)}
          options={primaryProbeSetOptions}
          isOptionDisabled={() => primaryProbeSetIds.length >= 2}
        />
        <Form.Text className="text-muted">
          Select the user action or feature that you are measuring with this
          experiment. You may select up to 2 primary probe sets.
        </Form.Text>
        <FormErrors name="primaryProbeSetIds" />
      </Form.Group>

      <Form.Group
        controlId="secondaryProbeSetIds"
        data-testid="secondary-probe-sets"
      >
        <Form.Label>
          Secondary Probe sets{" "}
          <Info
            data-tip={SECONDARY_PROBE_SETS_TOOLTIP}
            data-testid="tooltip-secondary-probe-sets"
            width="20"
            height="20"
            className="ml-1"
          />
        </Form.Label>
        <Select
          isMulti
          {...formSelectAttrs("secondaryProbeSetIds", setSecondaryProbeSetIds)}
          options={secondaryProbeSetOptions}
        />
        <Form.Text className="text-muted">
          Select the user action or feature that you are measuring with this
          experiment.
        </Form.Text>
        <FormErrors name="secondaryProbeSetIds" />
      </Form.Group>

      <div className="d-flex flex-row-reverse bd-highlight">
        {onNext && (
          <div className="p-2">
            <button
              onClick={handleNext}
              className="btn btn-secondary"
              disabled={isLoading}
              data-sb-kind="pages/EditMetrics"
            >
              Next
            </button>
          </div>
        )}
        <div className="p-2">
          <button
            data-testid="submit-button"
            type="submit"
            onClick={handleSubmit(handleSubmitAfterValidation)}
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
