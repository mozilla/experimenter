/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import { LocationProvider } from "@reach/router";
import AppLayoutWithSidebar from ".";

test("renders app layout content with children", () => {
  render(
    <LocationProvider>
      <AppLayoutWithSidebar>
        <p data-testid="test-child">Hello, world!</p>
      </AppLayoutWithSidebar>
    </LocationProvider>,
  );
  expect(screen.getByTestId("AppLayoutWithSidebar")).toBeInTheDocument();
  expect(screen.getByTestId("test-child")).toBeInTheDocument();
});
