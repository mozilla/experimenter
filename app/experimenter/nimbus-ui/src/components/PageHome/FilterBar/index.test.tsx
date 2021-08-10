/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render } from "@testing-library/react";
import React from "react";
import { EVERYTHING_SELECTED_VALUE, Subject } from "../mocks";

describe("FilterBar", () => {
  it("renders as expected", () => {
    render(<Subject value={EVERYTHING_SELECTED_VALUE} />);
  });
});
