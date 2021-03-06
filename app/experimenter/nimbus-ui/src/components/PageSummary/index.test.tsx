/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import PageSummary from ".";
import { mockExperimentQuery } from "../../lib/mocks";
import { RouterSlugProvider } from "../../lib/test-utils";

const { mock, experiment } = mockExperimentQuery("demo-slug");

describe("PageSummary", () => {
  it("renders as expected", async () => {
    render(
      <RouterSlugProvider mocks={[mock]}>
        <PageSummary />
      </RouterSlugProvider>,
    );

    await screen.findByTestId("PageSummary");
    screen.getByRole("navigation");
    screen.getByRole("heading", { name: experiment.name });
  });
});
