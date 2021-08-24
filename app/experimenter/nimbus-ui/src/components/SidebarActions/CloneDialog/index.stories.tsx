/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { action } from "@storybook/addon-actions";
import { withLinks } from "@storybook/addon-links";
import React from "react";
import CloneDialog from ".";
import { mockExperimentQuery } from "../../../lib/mocks";

export default {
  title: "components/SidebarActions/CloneDialog",
  component: CloneDialog,
  decorators: [withLinks],
};

const { experiment } = mockExperimentQuery("my-special-slug");

export const Shown = () => {
  const onClose = action("close");
  const onClone = action("clone");
  return (
    <div>
      <p>Background content.</p>
      <CloneDialog
        {...{
          experiment,
          show: true,
          onCancel: onClose,
          onSave: onClone,
          isLoading: false,
          isServerValid: true,
          submitErrors: {},
          setSubmitErrors: () => {},
        }}
      />
    </div>
  );
};
