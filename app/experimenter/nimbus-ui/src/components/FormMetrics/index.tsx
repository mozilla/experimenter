/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import Form from "react-bootstrap/Form";
import Alert from "react-bootstrap/Alert";
import { getExperiment } from "../../types/getExperiment";
import { getConfig_nimbusConfig_probeSets } from "../../types/getConfig";
import { useExitWarning } from "../../hooks";
import Select, { ActionMeta, ValueType } from "react-select";

type SelectOption = { label: string; value: string };

type FormMetricsProps = {
  experiment: getExperiment["experimentBySlug"];
  probeSets: (getConfig_nimbusConfig_probeSets | null)[] | null;
  isLoading: boolean;
  isServerValid: boolean;
  submitErrors: Record<string, string[]>;
  onSave: (data: Record<string, any>, reset: Function) => void;
  onNext: (ev: React.FormEvent) => void;
};

const FormMetrics = ({
  experiment,
  probeSets,
  isLoading,
  isServerValid,
  submitErrors,
  onSave,
  onNext,
}: FormMetricsProps) => {
  const { handleSubmit, reset, formState } = useForm({
    mode: "onTouched",
  });
  const { isSubmitted, isDirty } = formState;
  const [selectedPrimaryProbeSetIds, setSelectedPrimaryProbeSetIds] = useState<
    string[]
  >(experiment?.primaryProbeSets?.map((p) => p?.id as string) || []);
  const [
    selectedSecondaryProbeSetsIds,
    setselectedSecondaryProbeSetsIds,
  ] = useState<string[]>(
    experiment?.secondaryProbeSets?.map((p) => p?.id as string) || [],
  );

  const isValid = isServerValid && formState.isValid;
  const isDirtyUnsaved = isDirty && !(isValid && isSubmitted);

  const shouldWarnOnExit = useExitWarning();
  useEffect(() => {
    shouldWarnOnExit(isDirtyUnsaved);
  }, [shouldWarnOnExit, isDirtyUnsaved]);

  const handleSubmitAfterValidation = useCallback(() => {
    if (isLoading) return;
    onSave(
      {
        primaryProbeSetIds: selectedPrimaryProbeSetIds,
        secondaryProbeSetIds: selectedSecondaryProbeSetsIds,
      },
      reset,
    );
  }, [
    isLoading,
    onSave,
    reset,
    selectedPrimaryProbeSetIds,
    selectedSecondaryProbeSetsIds,
  ]);

  const handleNext = useCallback(
    (ev: React.FormEvent) => {
      ev.preventDefault();
      onNext!(ev);
    },
    [onNext],
  );

  const handlePrimaryProbeSetsChange = (
    selectedOptions: SelectOption[] | null,
  ) => {
    const probeSetIds = selectedOptions?.map((option) => option?.value) || [];
    setSelectedPrimaryProbeSetIds(probeSetIds);
  };

  const handleSecondaryProbeSetsChange = (
    selectedOptions: SelectOption[] | null,
  ) => {
    const probeSetIds = selectedOptions?.map((option) => option?.value) || [];
    setselectedSecondaryProbeSetsIds(probeSetIds);
  };

  const primaryProbeSetOptions: SelectOption[] = [];
  const secondaryProbeSetOptions: SelectOption[] = [];

  if (probeSets) {
    for (const probeSet of probeSets) {
      if (probeSet) {
        if (!selectedSecondaryProbeSetsIds.includes(probeSet.id)) {
          primaryProbeSetOptions.push({
            label: probeSet.name,
            value: probeSet.id,
          });
        }
        if (!selectedPrimaryProbeSetIds.includes(probeSet.id)) {
          secondaryProbeSetOptions.push({
            label: probeSet.name,
            value: probeSet.id,
          });
        }
      }
    }
  }

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
        controlId="selectedPrimaryProbeSetIds"
        data-testid="primary-probe-sets"
      >
        <Form.Label>Primary Probe sets</Form.Label>
        <Select
          options={primaryProbeSetOptions}
          defaultValue={experiment?.primaryProbeSets?.map((p) => ({
            label: p?.name as string,
            value: p?.id as string,
          }))}
          onChange={
            handlePrimaryProbeSetsChange as (
              value: ValueType<SelectOption>,
              actionMeta: ActionMeta<SelectOption>,
            ) => void
          }
          isOptionDisabled={() => selectedPrimaryProbeSetIds.length >= 2}
          isMulti
        />
        <Form.Text className="text-muted">
          Select the user action or feature that you are measuring with this
          experiment. You may select up to 2 primary probe sets.
        </Form.Text>
      </Form.Group>

      <Form.Group
        controlId="selectedSecondaryProbeSetsIds"
        data-testid="secondary-probe-sets"
      >
        <Form.Label>Secondary Probe sets</Form.Label>
        <Select
          options={secondaryProbeSetOptions}
          defaultValue={experiment?.secondaryProbeSets?.map((p) => ({
            label: p?.name as string,
            value: p?.id as string,
          }))}
          onChange={
            handleSecondaryProbeSetsChange as (
              value: ValueType<SelectOption>,
              actionMeta: ActionMeta<SelectOption>,
            ) => void
          }
          isMulti
        />
        <Form.Text className="text-muted">
          Select the user action or feature that you are measuring with this
          experiment.
        </Form.Text>
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
