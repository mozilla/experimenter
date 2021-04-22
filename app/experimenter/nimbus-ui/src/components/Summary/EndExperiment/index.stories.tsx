/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import React from "react";
import { Subject } from "./mocks";

export default {
  title: "components/Summary/EndExperiment",
  component: Subject,
};

export const canRequestEnd = () => {
  const onSubmit = action("Confirm request end");
  return <Subject {...{ onSubmit }} />;
};

export const loadingDisabled = () => <Subject isLoading={true} />;
