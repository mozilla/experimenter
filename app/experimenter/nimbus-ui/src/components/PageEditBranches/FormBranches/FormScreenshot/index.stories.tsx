/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import FormScreenshot from ".";
import { Subject } from "./mocks";

export default {
  title: "pages/EditBranches/FormBranches/FormScreenshot",
  component: FormScreenshot,
};

const storyWithProps = (
  props?: React.ComponentProps<typeof Subject>,
  storyName?: string,
) =>
  Object.assign(() => <Subject {...props} />, {
    storyName,
  });

export const Basic = storyWithProps();
