/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import { SizingRecipe } from "@mozilla/nimbus-schemas";
import { render, screen } from "@testing-library/react";
import React from "react";
import PopulationSizingNoData from "src/components/PageEditAudience/PopulationSizingNoData";

describe("PopulationSizingNoData", () => {
  it("renders targets as expected", () => {
    const sizingRecipes: SizingRecipe[] = [
      {
        app_id: "firefox_desktop",
        channel: "release",
        locale: "('EN-US')",
        country: "US",
        new_or_existing: "new",
      },
      {
        app_id: "firefox_desktop",
        channel: "release",
        locale: "('EN-US')",
        language: undefined,
        country: "all",
        new_or_existing: "existing",
      },
    ];
    render(
      <PopulationSizingNoData
        availableTargets={sizingRecipes}
        applicationName="firefox_desktop"
      />,
    );

    expect(
      screen.getByText("Pre-computed population sizing data Not Available"),
    );
    expect(
      screen.getByTestId("population-sizing-nodata-info"),
    ).toHaveTextContent("firefox_desktop", { normalizeWhitespace: true });
    expect(
      screen.getByTestId("population-sizing-nodata-targets"),
    ).toHaveTextContent(
      '{ "channel": "release", "locale": "(\'EN-US\')", "country": "US" }{ "channel": "release", "locale": "(\'EN-US\')", "country": "all" }',
      { normalizeWhitespace: true },
    );
  });
  it("renders lack of targets as expected", () => {
    render(
      <PopulationSizingNoData availableTargets={[]} applicationName="fenix" />,
    );

    expect(
      screen.getByText("Pre-computed population sizing data Not Available"),
    );
    expect(
      screen.getByTestId("population-sizing-nodata-info"),
    ).toHaveTextContent("fenix", { normalizeWhitespace: true });
    expect(
      screen.getByTestId("population-sizing-nodata-targets"),
    ).toHaveTextContent(
      "No pre-computed sizing available for this application.",
      { normalizeWhitespace: true },
    );
  });
});
