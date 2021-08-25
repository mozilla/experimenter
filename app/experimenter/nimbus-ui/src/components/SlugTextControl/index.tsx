/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import Form from "react-bootstrap/Form";
import { slugify } from "./slugify";

export type SlugTextControlProps = {
  defaultValue?: string;
  value?: any;
};

export const SlugTextControl = ({
  value,
  defaultValue,
}: SlugTextControlProps) => (
  <Form.Control
    readOnly
    data-testid="SlugTextControl"
    value={slugify(value || defaultValue)}
    type="text"
  />
);

export default SlugTextControl;
