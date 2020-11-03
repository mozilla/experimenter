/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Button from "react-bootstrap/Button";

import { getExperiment_experimentBySlug } from "../../types/getExperiment";
import {
  getConfig_nimbusConfig,
  getConfig_nimbusConfig_featureConfig,
} from "../../types/getConfig";

import FormBranch from "./FormBranch";

import {
  useFormBranchesReducer,
  FormBranchesSaveState,
  REFERENCE_BRANCH_IDX,
  AnnotatedBranch,
  extractSaveState,
} from "./reducer";

export const FormBranches = ({
  experiment,
  featureConfig,
  onSave,
  onNext,
}: {
  experiment: getExperiment_experimentBySlug;
  featureConfig: getConfig_nimbusConfig["featureConfig"];
  onSave: (state: FormBranchesSaveState) => void;
  onNext: () => void;
}) => {
  const [formBranchesState, dispatch] = useFormBranchesReducer(experiment);
  const {
    featureConfig: experimentFeatureConfig,
    referenceBranch,
    treatmentBranches,
    equalRatio,
  } = formBranchesState;

  const handleAddBranch = () => dispatch({ type: "addBranch" });

  const handleRemoveBranch = (idx: number) => () =>
    dispatch({ type: "removeBranch", idx });

  const handleUpdateBranch = (idx: number) => (value: AnnotatedBranch) =>
    dispatch({ type: "updateBranch", idx, value });

  const handleEqualRatioChange = (ev: React.ChangeEvent<HTMLInputElement>) =>
    dispatch({ type: "setEqualRatio", value: ev.target.checked });

  // HACK: just use the first available feature config when adding
  // The only available indicator whether to display "Add feature config" is a non-null feature config
  const handleAddFeatureConfig = () =>
    dispatch({ type: "setFeatureConfig", value: featureConfig![0] });

  const handleRemoveFeatureConfig = () =>
    dispatch({ type: "removeFeatureConfig" });

  const handleFeatureConfigChange = (
    value: getConfig_nimbusConfig_featureConfig | null,
  ) => dispatch({ type: "setFeatureConfig", value });

  // TODO: EXP-505 implement save button enable/disable logic
  const isSaveDisabled = false;

  const handleSaveClick = (
    ev: React.MouseEvent<HTMLButtonElement, MouseEvent>,
  ) => {
    ev.preventDefault();
    onSave(extractSaveState(formBranchesState));
  };

  // TODO: EXP-505 implement next button enable/disable logic
  const isNextDisabled = false;

  const handleNextClick = (
    ev: React.MouseEvent<HTMLButtonElement, MouseEvent>,
  ) => {
    ev.preventDefault();
    onNext();
  };

  const commonBranchProps = {
    equalRatio,
    featureConfig,
    experimentFeatureConfig,
    onFeatureConfigChange: handleFeatureConfigChange,
    onAddFeatureConfig: handleAddFeatureConfig,
    onRemoveFeatureConfig: handleRemoveFeatureConfig,
  };

  return (
    <section data-testid="FormBranches" className="border-top my-3">
      <Form className="p-2">
        <Form.Row className="my-3">
          <Form.Group controlId="evenRatio">
            <Form.Check
              data-testid="equal-ratio-checkbox"
              onChange={handleEqualRatioChange}
              checked={equalRatio}
              type="checkbox"
              label="Users should be split evenly between all branches"
            />
          </Form.Group>
          <Form.Group as={Col} className="align-top text-right">
            <Button
              data-testid="add-branch"
              variant="outline-primary"
              size="sm"
              onClick={handleAddBranch}
            >
              + Add branch
            </Button>
          </Form.Group>
        </Form.Row>
      </Form>
      <section>
        {referenceBranch && (
          <FormBranch
            {...{
              ...commonBranchProps,
              id: `branch-reference`,
              isReference: true,
              branch: { ...referenceBranch, __key: "branch-reference" },
              onChange: handleUpdateBranch(REFERENCE_BRANCH_IDX),
            }}
          />
        )}
        {treatmentBranches &&
          treatmentBranches.map(
            (branch, idx) =>
              branch && (
                <FormBranch
                  {...{
                    ...commonBranchProps,
                    key: branch.__key,
                    id: branch.__key,
                    branch,
                    onRemove: handleRemoveBranch(idx),
                    onChange: handleUpdateBranch(idx),
                  }}
                />
              ),
          )}
      </section>

      <div className="d-flex flex-row-reverse bd-highlight">
        <div className="p-2">
          <button
            data-testid="next-button"
            className="btn btn-secondary"
            disabled={isNextDisabled}
            onClick={handleNextClick}
          >
            Next
          </button>
        </div>
        <div className="p-2">
          <button
            data-testid="save-button"
            type="submit"
            className="btn btn-primary"
            disabled={isSaveDisabled}
            onClick={handleSaveClick}
          >
            <span>Save</span>
          </button>
        </div>
      </div>
    </section>
  );
};

export default FormBranches;
