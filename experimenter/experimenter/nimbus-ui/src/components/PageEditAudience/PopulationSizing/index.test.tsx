/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import PopulationSizing from "src/components/PageEditAudience/PopulationSizing";
import { MOCK_SIZING_DATA } from "src/lib/visualization/mocks";

describe("PopulationSizing", () => {
  it("renders errors as expected", () => {
    const sizingData = MOCK_SIZING_DATA;
    const totalNewClients = 10000;
    const totalExistingClients = 100000;
    render(
      <PopulationSizing
        sizingData={sizingData}
        totalNewClients={totalNewClients}
        totalExistingClients={totalExistingClients}
      />,
    );

    expect(screen.getByText("Pre-computed population sizing data"));
    expect(screen.getByTestId("new-total-clients-label")).toHaveTextContent(
      `${totalNewClients} total`,
    );
    expect(
      screen.getByTestId("existing-total-clients-label"),
    ).toHaveTextContent(`${totalExistingClients} total`);

    expect(screen.getAllByText("Percent of clients:")).toHaveLength(12);
    expect(screen.getAllByText("Expected number of clients:")).toHaveLength(12);
  });
});
