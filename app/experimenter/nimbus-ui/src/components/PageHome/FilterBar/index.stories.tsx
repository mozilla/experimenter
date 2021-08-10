/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import FilterBar from ".";
import { EVERYTHING_SELECTED_VALUE, Subject } from "../mocks";

const withPadding = (Story: React.FC) => (
  <div className="p-3">
    <Story />
  </div>
);

export default {
  title: "pages/Home/FilterBar",
  component: FilterBar,
  decorators: [withPadding],
};

export const NothingSelected = () => <Subject />;

export const EverythingSelected = () => (
  <Subject value={EVERYTHING_SELECTED_VALUE} />
);
