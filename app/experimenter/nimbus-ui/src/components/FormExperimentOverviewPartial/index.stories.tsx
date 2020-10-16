/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { storiesOf } from "@storybook/react";
import { action } from "@storybook/addon-actions";
import FormExperimentOverviewPartial from ".";

const APPLICATIONS = ["firefox-desktop", "fenix", "reference-browser"];

storiesOf("components/FormExperimentOverviewPartial", module).add(
  "basic",
  () => <Subject />,
);

const Subject = ({
  onSubmit = action("onSubmit"),
  onCancel = action("onCancel"),
  applications = APPLICATIONS,
} = {}) => (
  <FormExperimentOverviewPartial {...{ onSubmit, onCancel, applications }} />
);
