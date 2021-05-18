/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import Row from "react-bootstrap/Row";
import { useCommonForm } from "../../hooks";

type InputRadiosProps = {
  children: React.ReactNode;
  name: string;
  options: {
    label: string;
    value: string;
  }[];
  FormErrors: ReturnType<typeof useCommonForm>["FormErrors"];
  formControlAttrs: ReturnType<typeof useCommonForm>["formControlAttrs"];
};

export const InputRadios: React.FC<InputRadiosProps> = ({
  children,
  name,
  options,
  FormErrors,
  formControlAttrs,
}) => (
  <Form.Group controlId={name} as={Container}>
    <Row className="align-items-center mt-4 mb-4">
      <Col sm={10} className="col-sm-10 pl-0">
        <Form.Label className="mb-0">{children}</Form.Label>
        <FormErrors {...{ name }} />
      </Col>

      <Col sm={2} className="d-flex justify-content-end pr-0">
        {options.map((option) => (
          <span className="ml-3" key={`radio-${name}-${option.value}`}>
            <Form.Check
              type="radio"
              value={option.value}
              label={option.label}
              id={`${name}-${option.value}`}
              {...formControlAttrs(name, {}, false)}
            />
          </span>
        ))}
      </Col>
    </Row>
  </Form.Group>
);

export default InputRadios;
