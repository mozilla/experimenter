/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useRef } from "react";
import Form from "react-bootstrap/Form";
import LinkExternal from "src/components/LinkExternal";
import { EXTERNAL_URLS } from "src/lib/constants";

const checkboxLabels = [
  "I understand the risks associated with launching an experiment",
  "I have gone through the",
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
      onChange(
        checkboxLabels.every(
          (label) => !!checkedBoxes.current[label as string],
        ),
      );
    };

  return (
    <Form.Row className="mx-1 my-3 text-body">
      {checkboxLabels.map((labelText, index) => (
        <Form.Group
          key={index}
          id="checkbox"
          className="w-100 my-1"
          controlId={`checkbox-${index}`}
        >
          <Form.Check
            type="checkbox"
            label={
              <>
                {labelText}{" "}
                {index === 1 && (
                  <LinkExternal href={EXTERNAL_URLS.TRAINING_AND_PLANNING_DOC}>
                    experiment onboarding program
                  </LinkExternal>
                )}
              </>
            }
            onChange={handleConfirmChange(labelText)}
            {...{ "data-testid": "required-checkbox" }}
          />
        </Form.Group>
      ))}
    </Form.Row>
  );
};

export default FormLaunchConfirmationCheckboxes;
