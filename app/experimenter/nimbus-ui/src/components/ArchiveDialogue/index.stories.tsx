/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action, withActions } from "@storybook/addon-actions";
import React from "react";
import ArchiveDialogue from ".";
import { Subject } from "./mocks";

export default {
  title: "components/ArchiveDialogue",
  component: ArchiveDialogue,
  decorators: [withActions],
};

const onClose = action("close");
const refetch = action("refetch") as () => Promise<any>;

export const basic = () => <Subject {...{ onClose, refetch }} />;
