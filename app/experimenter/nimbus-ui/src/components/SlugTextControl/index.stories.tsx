/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState } from "react";
import Form from "react-bootstrap/Form";
import SlugTextControl from ".";

export default {
  title: "components/SlugTextControl",
  component: SlugTextControl,
};

export const Basic = () => {
  const defaultName = "This is a test";
  const [name, setName] = useState(defaultName);
  return (
    <Form className="p-3" onSubmit={() => {}}>
      <Form.Group controlId="name">
        <Form.Label>Public name</Form.Label>
        <Form.Control
          {...{
            type: "text",
            value: name,
            onChange: (ev) => setName(ev.target.value),
          }}
        />
        <Form.Text className="text-muted">
          This name will be public to users in about:studies.
        </Form.Text>
      </Form.Group>
      <Form.Group controlId="name">
        <Form.Label>Slug</Form.Label>
        <SlugTextControl value={name} defaultValue={defaultName} />
        <Form.Text className="text-muted">
          This is a unique identifier based on the public name.
        </Form.Text>
      </Form.Group>
    </Form>
  );
};
