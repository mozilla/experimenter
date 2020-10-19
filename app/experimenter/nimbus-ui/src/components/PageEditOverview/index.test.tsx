/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import React from "react";
import { render, screen } from "@testing-library/react";
import PageEditOverview from ".";
import { LocationProvider } from "@reach/router";

describe("PageEditOverview", () => {
  const Subject = () => {
    return (
      <LocationProvider>
        <PageEditOverview />
      </LocationProvider>
    );
  };

  it("renders as expected", () => {
    render(<Subject />);
    expect(screen.getByTestId("PageEditOverview")).toBeInTheDocument();
  });
});
