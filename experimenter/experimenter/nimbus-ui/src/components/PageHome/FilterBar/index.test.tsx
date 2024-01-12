/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import {
  EVERYTHING_SELECTED_VALUE,
  FilterSelectSubject,
  Subject,
} from "src/components/PageHome/mocks";
import { MockedCache } from "src/lib/mocks";

describe("FilterBar", () => {
  it("renders as expected", () => {
    render(
      <MockedCache>
        <Subject value={EVERYTHING_SELECTED_VALUE} />
      </MockedCache>,
    );
  });
});

describe("FilterSelect", () => {
  it("pluralizes the filter names correctly", () => {
    render(
      <MockedCache>
        <FilterSelectSubject
          filterValueName="qaStatus"
          fieldLabel="QA Status"
          fieldOptions={EVERYTHING_SELECTED_VALUE.qaStatus!}
        />
      </MockedCache>,
    );

    expect(screen.queryByText("All QA Statuss")).not.toBeInTheDocument();
    expect(screen.queryByText("All QA Statuses")).toBeInTheDocument();
  });
});
