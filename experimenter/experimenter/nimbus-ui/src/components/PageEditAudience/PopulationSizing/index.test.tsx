/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { render, screen } from "@testing-library/react";
import React from "react";
import PopulationSizing from "src/components/PageEditAudience/PopulationSizing";
import { mockSizingData } from "src/lib/visualization/mocks";

describe("PopulationSizing", () => {
  it("renders errors as expected", () => {
    const sizingData = mockSizingData();
    const totalClients = 10000;
    render(
      <PopulationSizing sizingData={sizingData} totalClients={totalClients} />,
    );

    expect(screen.getByText("Pre-computed population sizing data"));
    expect(
      screen.getByText(`${totalClients} total clients for given parameters`),
    );

    expect(screen.getAllByText("Clients per branch")).toHaveLength(6);
  });
});
