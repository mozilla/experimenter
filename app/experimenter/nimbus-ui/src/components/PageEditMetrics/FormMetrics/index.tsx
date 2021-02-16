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
import {
  getExperiment,
  getExperiment_experimentBySlug_primaryProbeSets,
  getExperiment_experimentBySlug_secondaryProbeSets,
} from "../../../types/getExperiment";

export const metricsFieldNames = [
  "primaryProbeSetSlugs",
  "secondaryProbeSetSlugs",
] as const;

type FormMetricsProps = {
  experiment: getExperiment["experimentBySlug"];
  isLoading: boolean;
  isServerValid: boolean;
  submitErrors: Record<string, string[]>;
  setSubmitErrors: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  onSave: (data: Record<string, any>, next: boolean) => void;
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
}: FormMetricsProps) => {
  const { probeSets } = useConfig();

  const getProbeSetSlugs = (probeSets: ProbeSets) =>
    probeSets?.map((probeSet) => probeSet?.slug as string) || [];

  // We must alter primary probe set options when a secondary set is selected
  // to exclude the set from primary probe set options and vice versa
  const [primaryProbeSetSlugs, setPrimaryProbeSetSlugs] = useState<string[]>(
    getProbeSetSlugs(experiment?.primaryProbeSets!),
  );
  const [secondaryProbeSetSlugs, setSecondaryProbeSetSlugs] = useState<
    string[]
  >(getProbeSetSlugs(experiment?.secondaryProbeSets!));

  const probeSetOption = (probeSet: ProbeSet) => ({
    label: probeSet.name,
    value: probeSet.slug,
  });

  const primaryProbeSetOptions: SelectOption[] = [];
  const secondaryProbeSetOptions: SelectOption[] = [];

  // Get primary/secondary options from server-supplied array of probe sets
  probeSets?.forEach((probeSet) => {
    if (!secondaryProbeSetSlugs.includes(probeSet!.slug)) {
      primaryProbeSetOptions.push(probeSetOption(probeSet!));
    }
    if (!primaryProbeSetSlugs.includes(probeSet!.slug)) {
      secondaryProbeSetOptions.push(probeSetOption(probeSet!));
    }
  });

  const defaultValues = {
    primaryProbeSetSlugs:
      experiment?.primaryProbeSets?.map((probeSet) =>
        probeSetOption(probeSet!),
      ) || "",
    secondaryProbeSetSlugs:
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
                primaryProbeSetSlugs,
                secondaryProbeSetSlugs,
              },
              next,
            ),
        ),
      ),
    [
      isLoading,
      onSave,
      handleSubmit,
      primaryProbeSetSlugs,
      secondaryProbeSetSlugs,
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
        controlId="primaryProbeSetSlugs"
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
          {...formSelectAttrs("primaryProbeSetSlugs", setPrimaryProbeSetSlugs)}
          options={primaryProbeSetOptions}
          isOptionDisabled={() => primaryProbeSetSlugs.length >= 2}
        />
        <Form.Text className="text-muted">
          Select the user action or feature that you are measuring with this
          experiment. You may select up to 2 primary probe sets.
        </Form.Text>
        <FormErrors name="primaryProbeSetSlugs" />
      </Form.Group>

      <Form.Group
        controlId="secondaryProbeSetSlugs"
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
          {...formSelectAttrs(
            "secondaryProbeSetSlugs",
            setSecondaryProbeSetSlugs,
          )}
          options={secondaryProbeSetOptions}
        />
        <Form.Text className="text-muted">
          Select the user action or feature that you are measuring with this
          experiment.
        </Form.Text>
        <FormErrors name="secondaryProbeSetSlugs" />
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
