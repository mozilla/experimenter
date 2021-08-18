/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { useMutation } from "@apollo/client";
import React, { useCallback, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Form from "react-bootstrap/Form";
import { UPDATE_EXPERIMENT_MUTATION } from "../../gql/experiments";
import { useCommonForm } from "../../hooks";
import { CHANGELOG_MESSAGES, SUBMIT_ERROR } from "../../lib/constants";
import { ExperimentInput } from "../../types/globalTypes";
import { updateExperiment_updateExperiment as UpdateExperimentResult } from "../../types/updateExperiment";

export const ArchiveDialogue = ({
  experimentId,
  onClose,
  refetch,
}: {
  experimentId: number;
  onClose: () => void;
  refetch: () => Promise<any>;
}) => {
  const [updateExperimentOverview, { loading }] = useMutation<
    { updateExperiment: UpdateExperimentResult },
    { input: ExperimentInput }
  >(UPDATE_EXPERIMENT_MUTATION);

  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const [isServerValid, setIsServerValid] = useState(true);

  const onFormSubmit = useCallback(
    async ({ archiveReason }: Record<string, any>) => {
      try {
        const result = await updateExperimentOverview({
          variables: {
            input: {
              id: experimentId,
              changelogMessage: CHANGELOG_MESSAGES.ARCHIVING_EXPERIMENT,
              isArchived: true,
              archiveReason,
            },
          },
        });

        if (!result.data?.updateExperiment) {
          throw new Error("Save failed, no error available");
        }

        setIsServerValid(true);
        setSubmitErrors({});
        await refetch();
        onClose();
      } catch (error) {
        setSubmitErrors({ "*": SUBMIT_ERROR });
      }
    },
    [updateExperimentOverview, experimentId, refetch, onClose],
  );

  const { formControlAttrs, isValid, handleSubmit, isSubmitted } =
    useCommonForm<"archiveReason">(
      {},
      isServerValid,
      submitErrors,
      setSubmitErrors,
    );

  return (
    <Form
      noValidate
      onSubmit={handleSubmit(onFormSubmit)}
      validated={isSubmitted && isValid}
    >
      {submitErrors["*"] && (
        <Alert data-testid="submit-error" variant="warning">
          {submitErrors["*"]}
        </Alert>
      )}

      <Form.Group controlId="archiveReason">
        <Form.Control
          {...formControlAttrs("archiveReason")}
          placeholder="Reason for archiving (optional)"
          as="textarea"
          rows={3}
        />
      </Form.Group>

      <div className="d-flex flex-row-reverse justify-content-between">
        <button
          type="submit"
          onClick={handleSubmit(onFormSubmit)}
          className="btn btn-primary"
          id="submit-button"
          disabled={loading}
        >
          <span>{loading ? "Saving" : "Save"}</span>
        </button>
        <button onClick={onClose} className="btn btn-secondary" type="button">
          Cancel
        </button>
      </div>
    </Form>
  );
};

export default ArchiveDialogue;
