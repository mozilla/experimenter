/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useRef } from "react";
import Form from "react-bootstrap/Form";

const checkboxLabels = [
  "I understand the risks associated with launching an experiment",
  "I have gone through the experiment onboarding program",
];

const FormLaunchConfirmationCheckboxes = ({
  onChange,
}: {
  onChange: (allChecked: boolean) => void;
}) => {
  const checkedBoxes = useRef<Record<string, boolean>>({});
  const handleConfirmChange =
    (labelText: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
      event.persist();
      checkedBoxes.current[labelText] = event.target.checked;
      onChange(checkboxLabels.every((label) => !!checkedBoxes.current[label]));
    };

  return (
    <Form.Row className="mx-1 my-3 text-body">
      {checkboxLabels.map((labelText, index) => (
        <Form.Group
          key={index}
          className="w-100 my-1"
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
  );
};

export default FormLaunchConfirmationCheckboxes;
