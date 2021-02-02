/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useState, useCallback } from "react";
import { storiesOf } from "@storybook/react";
import { ProtoForm, TestCases } from "./helpers";
import { Container, Alert } from "react-bootstrap";
import LinkExternal from "../../../src/components/LinkExternal";
import InlineErrorIcon from "../../../src/components/InlineErrorIcon";

const MODELS_URL =
  "https://github.com/mozilla/experimenter/blob/main/app/experimenter/experiments/models/nimbus.py";

storiesOf("Design Docs/Form Validation", module)
  .add("client-side validation", () => {
    const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});

    return (
      <Container className="pt-5">
        <h2>Client-side Validation</h2>
        <p>
          Client-side validation should be used to prevent invalid mutations
          from being attempted (i.e. the wrong type or fields that cannot be{" "}
          <code>null</code> in the{" "}
          <LinkExternal href={MODELS_URL}>database</LinkExternal>
          ). It should be used to validate fields that are required for launch
          or to duplicate server-side validation.
        </p>

        <ProtoForm
          demoInputs={[
            {
              name: "name",
              label: "Branch Name",
              defaultValue: "",
              required: true,
            },
          ]}
          isLoading={false}
          isServerValid
          submitErrors={submitErrors}
          setSubmitErrors={setSubmitErrors}
          onSubmit={() => {}}
        />

        <TestCases>
          <tr>
            <td>Clear the input and click elsewhere</td>
            <td>
              The input should be marked invalid and an error message should
              appear.
            </td>
          </tr>
          <tr>
            <td>With the input still empty, click Save</td>
            <td>
              The input should focused and the error message should still
              appear.
              <Alert variant="danger">
                The Save button should not be disabled if there are error
                messages – instead, you should draw attention to the invalid
                fields when the Save button is clicked.
              </Alert>
            </td>
          </tr>
          <tr>
            <td>Start typing in the input</td>
            <td>The input should become valid again.</td>
          </tr>
        </TestCases>
      </Container>
    );
  })
  .add("required for launch", () => {
    const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});

    return (
      <Container className="pt-5">
        <h2>Required for launch</h2>
        <p>
          Some fields like <code>publicDescription</code> are allowed to be{" "}
          <code>null</code> while someone is editing a draft, but must be set
          before the experiment can move to the review status. You should NOT
          mark these fields <code>required</code>, but rather add an{" "}
          <code>InlineErrorIcon</code> (
          <InlineErrorIcon
            name="example"
            message="A tooltip hint about this being required to launch"
          />
          ) with a tooltip indicating they must be filled out before launch.
        </p>
        <ProtoForm
          demoInputs={[
            {
              name: "name",
              label: "Totally optional field",
              defaultValue: "",
            },
            {
              name: "publicDescription",
              label: "Public Description",
              defaultValue: "",
              requiredAtLaunch: true,
            },
          ]}
          isLoading={false}
          isServerValid
          {...{ submitErrors, setSubmitErrors }}
          onSubmit={() => {}}
        />

        <TestCases>
          <tr>
            <td>Type something in the Public Description field.</td>
            <td>The warning icon should disappear</td>
          </tr>
          <tr>
            <td>Remove all the text from the Public Description field.</td>
            <td>The warning icon should show up again.</td>
          </tr>
        </TestCases>
      </Container>
    );
  })
  .add("server-side validation", () => {
    const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
    const [isServerValid, setIsServerValid] = useState(true);
    const [isLoading, setLoading] = useState(false);

    const onFormSubmit = useCallback(async ({ name }: Record<string, any>) => {
      setLoading(true);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setLoading(false);
      if (name === "really common name") {
        setIsServerValid(false);
        setSubmitErrors({ name: ["That name is taken."] });
      } else {
        setSubmitErrors({});
        setIsServerValid(true);
      }
    }, []);

    return (
      <Container className="pt-5">
        <h2>Server-side Validation</h2>
        <p>
          In general, validation (other than required values and type checking)
          should be done server-side at Save/Submit time.
        </p>

        <ProtoForm
          demoInputs={[
            { name: "name", label: "Name", defaultValue: "really common name" },
          ]}
          isLoading={false}
          isServerValid={isServerValid}
          {...{ submitErrors, setSubmitErrors }}
          setSubmitErrors={setSubmitErrors}
          onSubmit={onFormSubmit}
        />

        <TestCases>
          <tr>
            <td>
              Press the <code>Save</code> button. (The input value should be{" "}
              <code>really common name</code>, which the fake server will reject
              as already taken).
            </td>
            <td>
              The button should say <code>Saving</code> and be disabled while
              the server is waiting to respond. <br />
              The input is marked as invalid and has an error message.
            </td>
          </tr>
          <tr>
            <td>Change the text to something else.</td>
            <td>
              As you start typing, the input should be marked as valid again and
              the error message should disapear.
            </td>
          </tr>
          <tr>
            <td>Re-submit the form</td>
            <td>The input should remain in a valid state.</td>
          </tr>
        </TestCases>
      </Container>
    );
  });
