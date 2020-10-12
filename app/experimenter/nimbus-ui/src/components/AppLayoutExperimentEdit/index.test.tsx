/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import AppLayoutExperimentEdit from ".";

test("renders app layout content with children", () => {
  render(
    <AppLayoutExperimentEdit>
      <p data-testid="test-child">Hello, world!</p>
    </AppLayoutExperimentEdit>,
  );
  expect(screen.getByTestId("main")).toBeInTheDocument();
  expect(screen.getByTestId("test-child")).toBeInTheDocument();
});
