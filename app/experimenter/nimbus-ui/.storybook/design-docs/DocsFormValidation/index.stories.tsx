/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React, { useCallback, useState } from "react";
import { Alert, Container } from "react-bootstrap";
import LinkExternal from "../../../src/components/LinkExternal";
import { ProtoForm, TestCases } from "./helpers";

const MODELS_URL =
  "https://github.com/mozilla/experimenter/blob/main/app/experimenter/experiments/models/nimbus.py";

export default {
  title: "Design Docs/Form Validation",
};

export const ClientSide = () => {
  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});

  return (
    <Container className="pt-5">
      <h2>Client-side Validation</h2>
      <p>
        Client-side validation should be used to prevent invalid mutations from
        being attempted (i.e. the wrong type or fields that cannot be{" "}
        <code>null</code> in the{" "}
        <LinkExternal href={MODELS_URL}>database</LinkExternal>
        ). It should be used to validate fields that are required for launch or
        to duplicate server-side validation.
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
        reviewMessages={{}}
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
            The input should focused and the error message should still appear.
            <Alert variant="danger">
              The Save button should not be disabled if there are error messages
              – instead, you should draw attention to the invalid fields when
              the Save button is clicked.
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
};

export const ReviewReadiness = () => {
  return (
    <Container className="pt-5">
      <h2>Review-readiness</h2>
      <p>
        All fields are optional while an experiment is being worked on, but
        before it can be reviewed and launched there are fields that must be
        completed. This is configured in the backend in the{" "}
        <code>NimbusReadyForReviewSerializer</code>, so no additional work is
        necessary in the front-end beyond correctly setting field names.
      </p>

      <ProtoForm
        demoInputs={[
          { name: "name", label: "Name", defaultValue: "" },
          { name: "another_field", label: "Another Field", defaultValue: "" },
        ]}
        isServerValid={true}
        submitErrors={{}}
        setSubmitErrors={() => {}}
        isLoading={false}
        onSubmit={() => {}}
        reviewMessages={{
          name: ["This field cannot be empty."],
          another_field: ["Something's wrong with this one too eh"],
        }}
      />
    </Container>
  );
};

export const ServerSide = () => {
  const [submitErrors, setSubmitErrors] = useState<Record<string, any>>({});
  const [isServerValid, setIsServerValid] = useState(true);
  const [isLoading, setLoading] = useState(false);

  const onSubmit = useCallback(async ({ name }: Record<string, any>) => {
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 500));
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
        reviewMessages={{}}
        {...{
          onSubmit,
          submitErrors,
          setSubmitErrors,
          isServerValid,
          isLoading,
        }}
      />

      <TestCases>
        <tr>
          <td>
            Press the <code>Save</code> button. (The input value should be{" "}
            <code>really common name</code>, which the fake server will reject
            as already taken).
          </td>
          <td>
            The button should say <code>Saving</code> and be disabled while the
            server is waiting to respond. <br />
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
};
