/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import { Alert, Form } from "react-bootstrap";

type FormRequestReviewProps = {
  isLoading: boolean;
  submitError: string | null;
  onSubmit: () => void;
};

const checkboxLabels = [
  "I have gone through the experiment onboarding program",
  "I understand the risks associated with launching an experiment",
];

const FormRequestReview = ({
  isLoading,
  submitError,
  onSubmit,
}: FormRequestReviewProps) => {
  const [checkedBoxes, setCheckedBoxes] = useState<string[]>([]);
  const allBoxesChecked = checkboxLabels.every((element) =>
    checkedBoxes.includes(element),
  );

  const handleConfirmChange = (labelText: string) => (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    event.persist();
    setCheckedBoxes((existing) => {
      if (event.target.checked) {
        return [...existing, labelText];
      } else {
        return [...existing.filter((text) => text !== labelText)];
      }
    });
  };

  return (
    <Form className="py-2">
      {submitError && (
        <Alert data-testid="submit-error" variant="warning">
          {submitError}
        </Alert>
      )}

      <Form.Row className="my-3">
        {checkboxLabels.map((labelText, index) => (
          <Form.Group
            key={index}
            className="w-100"
            controlId={`checkbox-${index}`}
          >
            <Form.Check
              type="checkbox"
              label={labelText}
              onChange={handleConfirmChange(labelText)}
              {...{ "data-testid": "required-checkbox" }}
            />
          </Form.Group>
        ))}
      </Form.Row>

      <div className="d-flex bd-highlight">
        <div className="py-2">
          <button
            data-testid="submit-button"
            type="button"
            className="btn btn-secondary"
            disabled={isLoading || !allBoxesChecked}
            onClick={onSubmit}
          >
            Launch
          </button>
        </div>
      </div>
    </Form>
  );
};

export default FormRequestReview;
