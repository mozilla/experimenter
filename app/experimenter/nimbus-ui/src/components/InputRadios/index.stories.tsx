/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import InputRadios from ".";
import { useCommonForm } from "../../hooks";

const exampleFieldNames = ["foo"] as const;
const defaultValues = {
  foo: "true",
};

export default {
  title: "components/InputRadios",
  component: InputRadios,
};

// Because we're using a hook here this story function needs to be capitalized so it
// looks like a component, otherwise we get a react-hooks/rules-of-hooks warning
export const Basic = () => {
  const { FormErrors, formControlAttrs } = useCommonForm<
    typeof exampleFieldNames[number]
  >(defaultValues, true, {}, () => {});

  return (
    <InputRadios
      name="foo"
      options={[
        { label: "Yes", value: "true" },
        { label: "No", value: "false" },
      ]}
      {...{ FormErrors, formControlAttrs }}
    >
      Howdy, neighbor
    </InputRadios>
  );
};
