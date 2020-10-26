/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { action } from "@storybook/addon-actions";
import FormOverview from ".";

const APPLICATIONS = ["firefox-desktop", "fenix", "reference-browser"];

storiesOf("components/FormOverview", module)
  .add("basic", () => <Subject />)
  .add("loading", () => <Subject isLoading />)
  .add("errors", () => (
    <Subject
      submitErrors={{
        "*": "Big bad server thing broke!",
        name: "This name is terrible.",
        hypothesis: "You call this a hypothesis?",
        application: "That's a potato.",
      }}
    />
  ));

const Subject = ({
  isLoading = false,
  submitErrors = {},
  onSubmit = action("onSubmit"),
  onCancel = action("onCancel"),
  applications = APPLICATIONS,
} = {}) => (
  <div className="p-5">
    <FormOverview
      {...{ isLoading, submitErrors, onSubmit, onCancel, applications }}
    />
  </div>
);
